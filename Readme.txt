# 🎮 PyCraft

> A Minecraft-inspired voxel game built from scratch in Python using pure OpenGL.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![OpenGL](https://img.shields.io/badge/OpenGL-2.1+-red?logo=opengl)
![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey?logo=windows)
![License](https://img.shields.io/badge/License-MIT-green)

PyCraft is a fully playable 3D voxel sandbox game with procedural terrain, block breaking/placing, multiplayer support, and a complete account system — all written in Python with no game engine!

---

## ✨ Features

### 🌍 World
- **Procedural terrain** with custom Perlin noise (no external libraries needed)
- **5 biomes**: Plains, Desert, Forest, Mountains, Snow
- **Underground caves** and ore veins (coal, iron)
- **Trees** with different sizes per biome
- **Infinite chunk-based world** with seamless loading
- **World saving/loading** with chunk-level compression

### 🧱 Blocks (15 types)
- Grass, Dirt, Stone, Sand, Snow, Bedrock
- Wood, Planks, Leaves
- Cobblestone, Bricks, Glass
- Water (with proper transparency)
- Coal Ore, Iron Ore

### 🎮 Gameplay
- **First-person controls** with mouse look
- **Physics**: gravity, jumping, collision detection
- **Block interaction**: break with left click, place with right click
- **9-slot hotbar** with scroll wheel switching
- **Flying mode** for creative building
- **Sprint** with Shift key

### 👤 Account System
- Create accounts with password hashing (SHA-256)
- Auto-login on next launch
- Per-user profile folders

### 🌐 Multiplayer *(optional)*
- TCP client/server architecture
- Real-time player position sync
- Block updates broadcast to all players
- Built-in chat system
- Dedicated server mode

### 🎨 Texture Packs
- Load standard Minecraft-format texture packs
- Auto-generated procedural textures as fallback
- Simply drop packs into `texturepacks/` folder

### 🌍 Multi-Language Installer
- English, Русский, Українська, Беларуская
- Auto-downloads Python 3.12 if missing
- Auto-installs dependencies
- Creates desktop shortcuts

---

## 📦 Installation

### Option 1: Use the Installer (Recommended)

1. Download `PyCraft_Installer.exe` from [Releases](https://github.com/busy6813-arch/PyCraft/releases)
2. Double-click to run
3. Follow the wizard
4. Play from your Desktop shortcut!

### Option 2: Manual Install

```bash
# Install Python 3.10 or newer from python.org

# Install dependencies
pip install PyOpenGL glfw numpy Pillow

# Download the game
git clone https://github.com/busy6813-arch/PyCraft.git
cd PyCraft

# Run it
python PyCraft.py
