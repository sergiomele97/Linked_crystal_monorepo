<h1 align="center">💎 Linked Crystal</h1>
<p align="center"><em>Turning Pokémon Crystal into an MMO experience</em></p>

<table>
  <tr>
    <td valign="top">
      <h3 align="center">🚀 ROADMAP</h3>
      <img src="https://via.placeholder.com/400x1/FFFFFF/FFFFFF" alt="" width="140" height="1">
      <br>
      <details>
        <summary>About project origins</summary>
      <details>
        <summary>✅ 2020: The idea is born</summary>
        Probably around 2020 I discovered this bad boy called Pyboy. I was so hyped about that famouse video where one guy used genetic algorithms to teach a neuronal network to play Super Mario. That was way before LLMs and looked just amazing! I didnt even use git at the moment and had learnt Python just for bioinformatics. Somehow i reallized I could teoretically mimic an online experience for Pokemon Silver (my first and most favorite videogame) with the functions the pyboy API offered. Pyboy didnt even have sound nor color support at that moment. 
      </details>
      <br>
      <details>
        <summary>✅ 2023: Second iteration</summary>
        This time with pokemon crystal in mind (better pokemon diversity during the early game). I had to map the ram positions again as they're different for this rom. This time with color and a stronger programming background around 2023. But there was a little big problem: I play emulators on android laying on my sofa, not on desktop, which is way more unconfortable.
      </details>
      <br>
      <details>
        <summary>✅ Adapting pyboy to android</summary>
        By far the hardest and most uncertain thing I've done in this world. I was stuck here for a couple of years. Somehow it ended up working.
      </details>
      </details>
      <div>...</div>
      <br>
      <details>
        <summary>✅ Foundations</summary>
        <ul>
          <li>✅ Defining architecture</li>
          <li>✅ Integrating pyboy into an APK</li>
          <li>✅ Defining development environments</li>
        </ul>
      </details>
      <details>
        <summary>⚪ Developing backend MVP</summary>
        <ul>
          <li>⚪ Websockets and really eficient approach</li>
          <li>⚪ Centrilized server</li>
          <li>⚪ Sends info from all players to every player every 0.1 secs</li>
          <li>⚪ Easy to update data transfer model</li>
        </ul>
      </details>
      <details>
        <summary>⚪ Developing ram-drawing coordination</summary>
        <ul>
          <li>⚪ Defining the data transfer model</li>
          <li>⚪ Flawless drawing of the diferent players on screen</li>
        </ul>
      </details>
      <div>Will continue...</div>
    </td>
    <td valign="top">
      <h3 align="center">🌍 PRODUCTS AND ENVIRONMENTS</h3>    
      <img src="https://via.placeholder.com/400x1/FFFFFF/FFFFFF" alt="" width="600" height="1"><br>
      <table>
        <tr>
          <td>
            <a href="#1.1-set-up-local-client">Local client</a>
          </td>
          <td rowspan="6" align="center">
            <img src="https://raw.githubusercontent.com/sergiomele97/Linked_crystal_monorepo/main/.github/assets/flow.svg" width="300" alt="data flow animation">
          </td>
          <td>
            <a href="#1.2-set-up-local-server">Local server</a>
          </td>
        </tr>
        <tr>
            <td>
              <code><img height="30" width="100" src="https://img.shields.io/badge/Kivy-Desktop-brightgreen"></code><br>
              <code><img height="30" width="100" src="https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue"></code>
            </td>
            <td>
              <code><img height="60" width="100" src="https://img.shields.io/badge/Go-00ADD8?logo=Go&logoColor=white&style=for-the-badge"></code>
            </td>
        </tr>
        <tr>
          <td>
       <pre>
   |
   | Build APK
   |
   V  </pre>
          </td>
          <td>
       <pre>
   |
   | Deploy
   |
   V  </pre>
          </td>
        </tr>
        <tr>
          <td><b>Dev client</b></td>
          <td><b>Dev server</b></td>
        </tr>
        <tr>
          <td>
            <code><img height="30" width="100" src="https://img.shields.io/badge/Android-3DDC84?logo=android&logoColor=white"></code><br>         
            <code><img height="30" width="100" src="https://img.shields.io/badge/Kivy-Buildozer-blue?logo=python"></code><br>
            <code><img height="30" width="100" src="https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue"></code>
          </td>
          <td>
            <code><img height="30" width="100" src="https://img.shields.io/badge/Cloudflare-F38020?style=for-the-badge&logo=Cloudflare&logoColor=white"></code><br>
            <code><img height="60" width="100" src="https://img.shields.io/badge/Go-00ADD8?logo=Go&logoColor=white&style=for-the-badge"></code>
          </td>
        </tr>
      </table>
      <img src="https://via.placeholder.com/400x1/FFFFFF/FFFFFF" alt="" width="600" height="1"><br>
      <details>
        <summary><b>Production</b><br></summary>
          <br>
          <table>
              <tr>
                <td><b>Client</b></td>
                <td rowspan="2" align="center">
                  <img src="https://raw.githubusercontent.com/sergiomele97/Linked_crystal_monorepo/main/.github/assets/not_flow.svg" width="300" alt="data flow animation">
                </td>
                <td><b>Server</b></td>
              </tr>
              <tr>
                  <td>
                    Not published
                  </td>
                  <td>
                    Not deployed
                  </td>
              </tr>
          </table>
      </details>
      <img src="https://via.placeholder.com/400x1/FFFFFF/FFFFFF" alt="" width="600" height="1"><br>
      <br>
    </td>
    
  </tr>
</table>

# 1 Developing this project on your machine:

## Introduction: If you have 0 patience and are just a little bit familiar with docker I recommend you the one click ready environment: Containerized development environment on your web browser using webtops => (pending implementation)

Alternativaly, you can follow the classic method:
- We recommend Visual Studio Code as IDE.
- You will need a linux environment (or wsl in windows) in order to compile the client to an android APK using buildozer.

## 1.1 Set up local client
(pending)

## 1.2 Set up local server
(pending)

# 2 Development environment:

## 2.1 Compiling client to an Android APK
(pending steps)

## 2.2 Server deploy
The go server is currently self hosted with a cloudflare tunnel and automatically deployed on push via a yaml github actions pipeline.

# 3 Production (not yet implemented)
