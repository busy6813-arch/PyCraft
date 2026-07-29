
---

## 📄 `CHANGELOG.md`

```markdown
# 📋 Changelog

All notable changes to PyCraft will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Planned
- Sound effects
- Day/night cycle
- Mobs (pigs, cows, zombies)
- Crafting system
- Full inventory UI
- Command system

---

## [0.3.0] - 2024

### Added
- 🎨 **Texture pack support** - Load standard 16x16 PNG texture packs
- 🎨 **Procedural texture generator** - Auto-generates unique textures per block
  - Wood grain pattern
  - Brick pattern
  - Leaves with random gaps
  - Glass transparency
  - Noise variation on all blocks
- 📁 New `texturepacks/` folder in AppData
- 🖼️ Pillow (PIL) dependency for PNG loading

### Changed
- MeshBuilder now groups faces by texture for efficient rendering
- ChunkRenderer supports multiple textures per chunk
- World class now holds a reference to the active texture pack

---

## [0.2.5] - 2024

### Added
- 🎉 **Professional installer** with multi-language support
  - English 🇬🇧
  - Русский 🇷🇺
  - Українська 🇺🇦
  - Беларуская 🇧🇾
- 📥 Auto-downloads Python 3.12 if not installed
- 📦 Auto-installs PyOpenGL, glfw, numpy packages
- 🔗 Creates real .lnk shortcuts (Desktop + Start Menu)
- 🌐 Installer downloads latest game from GitHub
- 💾 Falls back to embedded base64 version if offline
- 🎨 Modern dark-themed installer UI

### Fixed
- Top faces of blocks not rendering (wrong vertex winding order)
- Fork-bomb risk if installer is run multiple times
- Cyrillic language display issues

---

## [0.2.0] - 2024

### Added
- 🌐 **Multiplayer support**
  - TCP client/server architecture
  - Real-time player position sync
  - Broadcast block updates
  - In-game chat system (press T)
  - Dedicated server mode (`--server` flag)
- 👥 See other players as red character models
- 💬 Chat history display

### Changed
- Networking uses pickle for serialization
- Server can be hosted from main game or standalone

---

## [0.1.5] - 2024

### Added
- 🌍 **Multi-biome world generation**
  - Plains (default)
  - Desert (sand-based)
  - Forest (dense trees)
  - Mountains (rocky peaks)
  - Snow (white surface)
- ⛰️ **Multi-octave Perlin noise** for realistic terrain
  - Continentalness layer (broad shapes)
  - Erosion layer (smooth/rough control)
  - Peaks & valleys layer
  - Detail noise for surface variation
- 🕳️ **Underground caves** using 3D noise
- ⛏️ **Ore generation**
  - Iron ore (deep, Y < 24)
  - Coal ore (mid, Y < 40)
- 🌲 **Biome-specific trees** (taller in forests)

### Removed
- ❌ Dependency on `noise` library (required C++ compiler on Windows)

### Added
- ✅ Custom pure-Python Perlin noise implementation

---

## [0.1.0] - 2024

### Added
- 🎮 **Initial release!**
- 🧱 15 block types (Grass, Dirt, Stone, Wood, Leaves, Sand, Water, etc.)
- 🎯 First-person controls with mouse look
- 🏃 Physics: gravity, jumping, collision detection
- 🖱️ Block breaking (left click) and placing (right click)
- 🎒 9-slot hotbar with scroll wheel switching
- ✈️ Flying mode (F key)
- 🔒 Account system with SHA-256 password hashing
- 💾 World saving to `%APPDATA%\PyCraft\saves\`
- 👤 Per-user account folders
- 🌊 Water rendering with transparency
- 🌫️ Distance fog for atmospheric effect
- 📝 Custom vector-based text renderer (no font files needed)
- 🎨 Modern dark UI menus
- 🔦 Simple lighting per face (top brightest, bottom darkest)

### Technical
- Pure Python 3.10+ implementation
- PyOpenGL for 3D rendering
- GLFW for window/input handling
- NumPy for fast chunk arrays
- 16x64x16 chunk size
- VBO-based rendering for performance
- 60 FPS locked with VSync

---

## Version Format

- **MAJOR** - Breaking changes (world save format changes)
- **MINOR** - New features, backwards compatible
- **PATCH** - Bug fixes only

---

[Unreleased]: https://github.com/busy6813-arch/PyCraft/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/busy6813-arch/PyCraft/releases/tag/v0.3.0
[0.2.5]: https://github.com/busy6813-arch/PyCraft/releases/tag/v0.2.5
[0.2.0]: https://github.com/busy6813-arch/PyCraft/releases/tag/v0.2.0
[0.1.5]: https://github.com/busy6813-arch/PyCraft/releases/tag/v0.1.5
[0.1.0]: https://github.com/busy6813-arch/PyCraft/releases/tag/v0.1.0
