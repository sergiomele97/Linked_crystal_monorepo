# 🚀 Welcome to the Project Wiki

Setting up a development environment for the first time can be so frustrating. You may spend 1 entire day without building any code.

Here we've made an effort to **automate everything**, so you don't have to go through that... but exceptions may always happen.

---

### 🚀 Getting Started
Run this:

```bash
git clone https://github.com/sergiomele97/Linked_crystal_monorepo
cd Linked_crystal_monorepo
make setup
```

> [!TIP]
> If you find any errors, just know they should be easy to fix by giving this context and the makefile contents to an **LLM (Gemini/ChatGPT)**.

>While you're computer is working, you can continue reading:

---

### 🛠️ Using the Makefile
The `makefile` at the root of the repo is just a definition of commands you can launch, either in:
* **The terminal** (Example: `make setup`)
* **The Visual Studio graphical interface** (Run and Debug)

You can check the commands available and what they do in the makefile.
>For example, you might clean reset your environment by executing `make clean`, you might run/debug the app by executing `make run-app`, or you might test the server by typing `make test-server`...

---

### 📱 Development Notes
* **Desktop:** Running the Python app or the Go server in desktop is really easy.
* **Android:** The tricky part is trying to build the **APK** (android executable) locally. It has really strict dependencies (Example: **Python 3.10**).

⚠️ **Important:** You should not try to change the dependencies or you will go crazy.
