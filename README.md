<table>
  <tr>
    <td valign="top">
      <h3 align="center">🚀 ROADMAP</h3>
      <img src="https://via.placeholder.com/400x1/FFFFFF/FFFFFF" alt="" width="140" height="1">
      <br>
      <details>
        <summary>✅ Paso 1: Planificación</summary>
        Definir objetivos y alcance del proyecto.  
        Reunir recursos y establecer cronograma.
      </details>
      <br>
      <details>
        <summary>✅ Paso 2: Diseño</summary>
        Crear diagramas, wireframes y especificaciones técnicas.
      </details>
      <br>
      <details>
        <summary>⚪ Paso 3: Desarrollo</summary>
        Implementar funcionalidades principales y pruebas iniciales.
      </details>
      <br>
      <details>
        <summary>⚪ Paso 4: Pruebas y QA</summary>
        Realizar pruebas exhaustivas y corrección de errores.
      </details>
      <br>
      <details>
        <summary>⚪ Paso 5: Lanzamiento</summary>
        Despliegue a producción y documentación final.
      </details>
        </td>
    <td valign="top">
      <h3 align="center">🌍 ENVIRONMENTS</h3>    
      <img src="https://via.placeholder.com/400x1/FFFFFF/FFFFFF" alt="" width="400" height="1">
      <br>
  
flowchart TD
    subgraph Local
        LBack[💻 Back: Servidor Go + WebSockets]
        LFront[🖥️ Front: App Desktop Python + Kivy]
        LBack --> LFront
        LFront -.-> LStatusLocal[⚪ Desplegado por cada dev]
    end

    subgraph Development
        DBack[🌐 Back: Servidor publicado]
        DFront[📱 Front: App Android compilada]
        DBack --> DFront
        DFront -.-> DStatusDev[✅ Healthy]
    end

    subgraph Producción
        PBack[❌ Back: No implementado]
        PFront[❌ Front: No implementado]
        PBack --> PFront
        PFront -.-> PStatusProd[⚪ Pendiente]
    end

    LFront --> DBack
    DFront --> PBack


      Información adicional, notas o recursos del proyecto
    </td>
  </tr>
</table>
