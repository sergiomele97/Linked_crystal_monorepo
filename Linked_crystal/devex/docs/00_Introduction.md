Setting up a development environment for the first time can be so frustating.
You may expend 1 entire day without building any code.

Here we've made an effort to automate everything, so you don't have to go through that... but exceptions may always happens.
The makefile at the root of the repo is just a definition of commands you can launch, either in the terminal (Exmaple: make setup) or in the visual studio graphical interface.
If you find any errors, just know they should be easy to fix by giving this context and te makefile contents to an LLM (Gemini-Chatgpt).
Running the python app or the go server in a desktop is really easy.
The tricky part is trying to build the apk (android executable) locally. It has really strict dependencies (Example: Python 3.10).
You should not try to change the dependencies or you will go crazy.

Run this:

git clone https://github.com/sergiomele97/Linked_crystal_monorepo
cd Linked_crystal_monorepo
make setup

While your computer works