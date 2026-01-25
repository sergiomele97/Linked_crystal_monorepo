package hub

import (
	"runtime"
	"sync"
	"sync/atomic"
	"syscall"
	"time"
)

// ------------------ MÉTRICAS ------------------

const (
	windowSize = 60
)

type MetricBucket struct {
	timestamp int64 // unix seconds
	recvCount int64
	sendCount int64
	latSum    int64 // nanoseconds
	latCount  int64
}

var (
	buckets   [windowSize]MetricBucket
	currentTs int64
)

func init() {
	currentTs = time.Now().Unix()
	go func() {
		ticker := time.NewTicker(time.Second)
		for t := range ticker.C {
			atomic.StoreInt64(&currentTs, t.Unix())
		}
	}()
}

func RecordMetrics(recv, send int, lat time.Duration) {
	now := atomic.LoadInt64(&currentTs)
	idx := now % windowSize
	bucket := &buckets[idx]

	// Si el bucket es viejo, intentamos resetearlo de forma atómica
	prevTime := atomic.LoadInt64(&bucket.timestamp)
	if prevTime != now {
		// Intentamos ser el que resetea el bucket para el nuevo segundo
		if atomic.CompareAndSwapInt64(&bucket.timestamp, prevTime, now) {
			atomic.StoreInt64(&bucket.recvCount, 0)
			atomic.StoreInt64(&bucket.sendCount, 0)
			atomic.StoreInt64(&bucket.latSum, 0)
			atomic.StoreInt64(&bucket.latCount, 0)
		}
		// Si perdimos el CAS, otro ya reseteó el bucket o estamos en el mismo segundo
		if atomic.LoadInt64(&bucket.timestamp) != now {
			return
		}
	}

	if recv > 0 {
		atomic.AddInt64(&bucket.recvCount, int64(recv))
	}
	if send > 0 {
		atomic.AddInt64(&bucket.sendCount, int64(send))
	}
	if lat > 0 {
		atomic.AddInt64(&bucket.latSum, int64(lat))
		atomic.AddInt64(&bucket.latCount, 1)
	}
}

func GetAverages() (recvRate, sendRate, latencyMs float64) {
	now := atomic.LoadInt64(&currentTs)
	cutoff := now - windowSize

	var recvTotal, sendTotal int64
	var latSumTotal int64
	var latCountTotal int64

	for i := 0; i < windowSize; i++ {
		ts := atomic.LoadInt64(&buckets[i].timestamp)
		if ts > cutoff && ts <= now {
			recvTotal += atomic.LoadInt64(&buckets[i].recvCount)
			sendTotal += atomic.LoadInt64(&buckets[i].sendCount)
			latSumTotal += atomic.LoadInt64(&buckets[i].latSum)
			latCountTotal += atomic.LoadInt64(&buckets[i].latCount)
		}
	}

	recvRate = float64(recvTotal) / float64(windowSize)
	sendRate = float64(sendTotal) / float64(windowSize)
	if latCountTotal > 0 {
		latencyMs = float64(latSumTotal) / float64(latCountTotal) / 1e6
	}
	return
}

type HardwareStats struct {
	MemPerClientKB float64 `json:"mem_per_client_kb"`
	TotalRSS_MB    float64 `json:"total_rss_mb"`
	CPU_Usage      float64 `json:"cpu_usage_percent"`
}

var (
	hwStatsMu sync.RWMutex
	hwStats   HardwareStats
)

// StartHardwareMonitor corre en segundo plano para no afectar el "hot path"
func StartHardwareMonitor() {
	ticker := time.NewTicker(5 * time.Second)
	var lastUsage syscall.Rusage
	var lastTime time.Time

	for now := range ticker.C {
		var m runtime.MemStats
		runtime.ReadMemStats(&m)

		// RSS (Resident Set Size) - RAM real usada
		rss := float64(m.Sys) / 1024 / 1024

		// Cálculo de CPU (User + System)
		var usage syscall.Rusage
		syscall.Getrusage(syscall.RUSAGE_SELF, &usage)

		cpuPercent := 0.0
		if !lastTime.IsZero() {
			deltaUser := usage.Utime.Sec - lastUsage.Utime.Sec + (usage.Utime.Usec-lastUsage.Utime.Usec)/1e6
			deltaSys := usage.Stime.Sec - lastUsage.Stime.Sec + (usage.Stime.Usec-lastUsage.Stime.Usec)/1e6
			deltaReal := now.Sub(lastTime).Seconds()
			cpuPercent = (float64(deltaUser) + float64(deltaSys)) / deltaReal * 100
		}

		// Contar clientes activos
		clientCount := 0
		clients.Range(func(_, _ any) bool { clientCount++; return true })

		hwStatsMu.Lock()
		hwStats.TotalRSS_MB = rss
		hwStats.CPU_Usage = cpuPercent
		if clientCount > 0 {
			hwStats.MemPerClientKB = (float64(m.Sys) / 1024) / float64(clientCount)
		} else {
			hwStats.MemPerClientKB = 0
		}
		hwStatsMu.Unlock()

		lastUsage = usage
		lastTime = now
	}
}

func GetHardwareStats() HardwareStats {
	hwStatsMu.RLock()
	defer hwStatsMu.RUnlock()
	return hwStats
}
