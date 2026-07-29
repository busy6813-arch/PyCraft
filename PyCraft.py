    # pycraft.py - PyCraft Main Entry Point
# Location: C:\Users\User\AppData\Roaming\PyCraft\pycraft.py

import sys
import os
import json
import hashlib
import struct
import math
import time
import random
import socket
import threading
import pickle
import uuid
import queue
from pathlib import Path
from collections import defaultdict

# Ensure paths exist
PYCRAFT_DIR = os.path.join(os.environ.get('APPDATA', '.'), 'PyCraft')
SAVES_DIR = os.path.join(PYCRAFT_DIR, 'saves')
USERS_DIR = os.path.join(PYCRAFT_DIR, 'Users')
os.makedirs(SAVES_DIR, exist_ok=True)
os.makedirs(USERS_DIR, exist_ok=True)
TEXTUREPACKS_DIR = os.path.join(PYCRAFT_DIR, 'texturepacks')
os.makedirs(TEXTUREPACKS_DIR, exist_ok=True)

import glfw
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


# ========================== PERLIN NOISE ==========================

class PerlinNoise:
    def __init__(self, seed=0):
        self.seed = seed
        rng = random.Random(seed)
        self.p = list(range(256))
        rng.shuffle(self.p)
        self.p = self.p + self.p
        self.grad3 = [
            (1,1,0),(-1,1,0),(1,-1,0),(-1,-1,0),
            (1,0,1),(-1,0,1),(1,0,-1),(-1,0,-1),
            (0,1,1),(0,-1,1),(0,1,-1),(0,-1,-1),
        ]

    @staticmethod
    def _fade(t):
        return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)

    @staticmethod
    def _lerp(t, a, b):
        return a + t * (b - a)

    def _grad3d(self, hash_val, x, y, z):
        g = self.grad3[hash_val % 12]
        return g[0] * x + g[1] * y + g[2] * z

    def _grad2d(self, hash_val, x, y):
        g = self.grad3[hash_val % 12]
        return g[0] * x + g[1] * y

    def noise2d(self, x, y):
        xi = int(math.floor(x)) & 255
        yi = int(math.floor(y)) & 255
        xf = x - math.floor(x)
        yf = y - math.floor(y)
        u = self._fade(xf)
        v = self._fade(yf)
        p = self.p
        aa = p[p[xi] + yi]
        ab = p[p[xi] + yi + 1]
        ba = p[p[xi + 1] + yi]
        bb = p[p[xi + 1] + yi + 1]
        x1 = self._lerp(u, self._grad2d(aa, xf, yf), self._grad2d(ba, xf - 1, yf))
        x2 = self._lerp(u, self._grad2d(ab, xf, yf - 1), self._grad2d(bb, xf - 1, yf - 1))
        return self._lerp(v, x1, x2)

    def noise3d(self, x, y, z):
        xi = int(math.floor(x)) & 255
        yi = int(math.floor(y)) & 255
        zi = int(math.floor(z)) & 255
        xf = x - math.floor(x)
        yf = y - math.floor(y)
        zf = z - math.floor(z)
        u = self._fade(xf)
        v = self._fade(yf)
        w = self._fade(zf)
        p = self.p
        aaa = p[p[p[xi] + yi] + zi]
        aba = p[p[p[xi] + yi + 1] + zi]
        aab = p[p[p[xi] + yi] + zi + 1]
        abb = p[p[p[xi] + yi + 1] + zi + 1]
        baa = p[p[p[xi + 1] + yi] + zi]
        bba = p[p[p[xi + 1] + yi + 1] + zi]
        bab = p[p[p[xi + 1] + yi] + zi + 1]
        bbb = p[p[p[xi + 1] + yi + 1] + zi + 1]
        x1 = self._lerp(u, self._grad3d(aaa, xf, yf, zf), self._grad3d(baa, xf-1, yf, zf))
        x2 = self._lerp(u, self._grad3d(aba, xf, yf-1, zf), self._grad3d(bba, xf-1, yf-1, zf))
        y1 = self._lerp(v, x1, x2)
        x1 = self._lerp(u, self._grad3d(aab, xf, yf, zf-1), self._grad3d(bab, xf-1, yf, zf-1))
        x2 = self._lerp(u, self._grad3d(abb, xf, yf-1, zf-1), self._grad3d(bbb, xf-1, yf-1, zf-1))
        y2 = self._lerp(v, x1, x2)
        return self._lerp(w, y1, y2)

    def octave2d(self, x, y, octaves=4, persistence=0.5, lacunarity=2.0):
        total = 0.0
        amplitude = 1.0
        frequency = 1.0
        max_val = 0.0
        for _ in range(octaves):
            total += self.noise2d(x * frequency, y * frequency) * amplitude
            max_val += amplitude
            amplitude *= persistence
            frequency *= lacunarity
        return total / max_val

    def octave3d(self, x, y, z, octaves=3, persistence=0.5, lacunarity=2.0):
        total = 0.0
        amplitude = 1.0
        frequency = 1.0
        max_val = 0.0
        for _ in range(octaves):
            total += self.noise3d(x * frequency, y * frequency, z * frequency) * amplitude
            max_val += amplitude
            amplitude *= persistence
            frequency *= lacunarity
        return total / max_val


# ========================== CONSTANTS ==========================

BLOCK_AIR = 0
BLOCK_GRASS = 1
BLOCK_DIRT = 2
BLOCK_STONE = 3
BLOCK_WOOD = 4
BLOCK_LEAVES = 5
BLOCK_SAND = 6
BLOCK_WATER = 7
BLOCK_COBBLESTONE = 8
BLOCK_PLANKS = 9
BLOCK_BEDROCK = 10
BLOCK_COAL_ORE = 11
BLOCK_IRON_ORE = 12
BLOCK_GLASS = 13
BLOCK_BRICK = 14
BLOCK_SNOW = 15

BLOCK_COLORS = {
    BLOCK_GRASS: (0.30, 0.78, 0.22),
    BLOCK_DIRT: (0.55, 0.36, 0.16),
    BLOCK_STONE: (0.50, 0.50, 0.50),
    BLOCK_WOOD: (0.45, 0.30, 0.10),
    BLOCK_LEAVES: (0.15, 0.55, 0.12),
    BLOCK_SAND: (0.88, 0.84, 0.58),
    BLOCK_WATER: (0.20, 0.40, 0.85),
    BLOCK_COBBLESTONE: (0.42, 0.42, 0.42),
    BLOCK_PLANKS: (0.70, 0.55, 0.30),
    BLOCK_BEDROCK: (0.15, 0.15, 0.15),
    BLOCK_COAL_ORE: (0.28, 0.28, 0.28),
    BLOCK_IRON_ORE: (0.60, 0.55, 0.50),
    BLOCK_GLASS: (0.75, 0.88, 0.95),
    BLOCK_BRICK: (0.68, 0.30, 0.22),
    BLOCK_SNOW: (0.94, 0.94, 0.98),
}

BLOCK_NAMES = {
    BLOCK_GRASS: "Grass", BLOCK_DIRT: "Dirt", BLOCK_STONE: "Stone",
    BLOCK_WOOD: "Wood", BLOCK_LEAVES: "Leaves", BLOCK_SAND: "Sand",
    BLOCK_WATER: "Water", BLOCK_COBBLESTONE: "Cobblestone",
    BLOCK_PLANKS: "Planks", BLOCK_BEDROCK: "Bedrock",
    BLOCK_COAL_ORE: "Coal Ore", BLOCK_IRON_ORE: "Iron Ore",
    BLOCK_GLASS: "Glass", BLOCK_BRICK: "Brick", BLOCK_SNOW: "Snow"
}

TRANSPARENT_BLOCKS = {BLOCK_AIR, BLOCK_WATER, BLOCK_GLASS, BLOCK_LEAVES}

CHUNK_SIZE = 16
CHUNK_HEIGHT = 64
RENDER_DISTANCE = 3
WATER_LEVEL = 20
GRAVITY = -22.0
JUMP_SPEED = 8.5
PLAYER_HEIGHT = 1.8
PLAYER_SPEED = 5.0
MOUSE_SENSITIVITY = 0.002
REACH_DISTANCE = 6.0
TARGET_FPS = 60
FRAME_TIME = 1.0 / TARGET_FPS


# ========================== ACCOUNT SYSTEM ==========================

class AccountManager:
    def __init__(self):
        self.accounts_file = os.path.join(USERS_DIR, 'accounts.json')
        self.session_file = os.path.join(PYCRAFT_DIR, 'session.json')
        self.accounts = self._load_accounts()
        self.current_user = None

    def _load_accounts(self):
        if os.path.exists(self.accounts_file):
            try:
                with open(self.accounts_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_accounts(self):
        with open(self.accounts_file, 'w') as f:
            json.dump(self.accounts, f, indent=2)

    @staticmethod
    def _hash_password(password):
        return hashlib.sha256(password.encode()).hexdigest()

    def create_account(self, username, password):
        if not username or not password:
            return False, "Username and password required"
        if username in self.accounts:
            return False, "Username already exists"
        if len(username) < 3:
            return False, "Username too short (min 3)"
        if len(password) < 4:
            return False, "Password too short (min 4)"
        user_folder = os.path.join(USERS_DIR, username)
        os.makedirs(user_folder, exist_ok=True)
        self.accounts[username] = {
            'password_hash': self._hash_password(password),
            'uuid': str(uuid.uuid4()),
            'created': time.time(),
            'last_login': time.time(),
            'play_time': 0
        }
        profile = {
            'username': username,
            'uuid': self.accounts[username]['uuid'],
            'created': self.accounts[username]['created'],
        }
        with open(os.path.join(user_folder, 'profile.json'), 'w') as f:
            json.dump(profile, f, indent=2)
        self._save_accounts()
        return True, "Account created successfully"

    def login(self, username, password):
        if username not in self.accounts:
            return False, "Account not found"
        if self.accounts[username]['password_hash'] != self._hash_password(password):
            return False, "Incorrect password"
        self.accounts[username]['last_login'] = time.time()
        self._save_accounts()
        self.current_user = username
        with open(self.session_file, 'w') as f:
            json.dump({'username': username}, f)
        return True, "Login successful"

    def auto_login(self):
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, 'r') as f:
                    data = json.load(f)
                    if data.get('username') in self.accounts:
                        self.current_user = data['username']
                        return True
            except Exception:
                pass
        return False

    def logout(self):
        self.current_user = None
        if os.path.exists(self.session_file):
            os.remove(self.session_file)


# ========================== TEXT RENDERING ==========================

class TextRenderer:
    _CHARS = None

    @classmethod
    def _init(cls):
        if cls._CHARS is not None:
            return
        C = {}
        C['A'] = [(0,0,0,5),(0,5,2,7),(2,7,4,5),(4,5,4,0),(0,3,4,3)]
        C['B'] = [(0,0,0,7),(0,7,3,7),(3,7,4,6),(4,6,3,4),(3,4,0,4),(0,0,3,0),(3,0,4,1),(4,1,4,3),(4,3,3,4)]
        C['C'] = [(4,1,3,0),(3,0,1,0),(1,0,0,1),(0,1,0,6),(0,6,1,7),(1,7,3,7),(3,7,4,6)]
        C['D'] = [(0,0,0,7),(0,7,3,7),(3,7,4,6),(4,6,4,1),(4,1,3,0),(3,0,0,0)]
        C['E'] = [(4,0,0,0),(0,0,0,7),(0,7,4,7),(0,4,3,4)]
        C['F'] = [(0,0,0,7),(0,7,4,7),(0,4,3,4)]
        C['G'] = [(4,6,3,7),(3,7,1,7),(1,7,0,6),(0,6,0,1),(0,1,1,0),(1,0,3,0),(3,0,4,1),(4,1,4,3),(4,3,2,3)]
        C['H'] = [(0,0,0,7),(4,0,4,7),(0,4,4,4)]
        C['I'] = [(1,0,3,0),(2,0,2,7),(1,7,3,7)]
        C['J'] = [(0,1,1,0),(1,0,3,0),(3,0,4,1),(4,1,4,7),(3,7,1,7)]
        C['K'] = [(0,0,0,7),(4,7,0,4),(0,4,4,0)]
        C['L'] = [(0,7,0,0),(0,0,4,0)]
        C['M'] = [(0,0,0,7),(0,7,2,4),(2,4,4,7),(4,7,4,0)]
        C['N'] = [(0,0,0,7),(0,7,4,0),(4,0,4,7)]
        C['O'] = [(1,0,0,1),(0,1,0,6),(0,6,1,7),(1,7,3,7),(3,7,4,6),(4,6,4,1),(4,1,3,0),(3,0,1,0)]
        C['P'] = [(0,0,0,7),(0,7,3,7),(3,7,4,6),(4,6,4,4),(4,4,3,3),(3,3,0,3)]
        C['Q'] = [(1,0,0,1),(0,1,0,6),(0,6,1,7),(1,7,3,7),(3,7,4,6),(4,6,4,1),(4,1,3,0),(3,0,1,0),(2,2,4,0)]
        C['R'] = [(0,0,0,7),(0,7,3,7),(3,7,4,6),(4,6,4,5),(4,5,3,4),(3,4,0,4),(2,4,4,0)]
        C['S'] = [(0,1,1,0),(1,0,3,0),(3,0,4,1),(4,1,4,3),(4,3,3,4),(3,4,1,4),(1,4,0,5),(0,5,0,6),(0,6,1,7),(1,7,3,7),(3,7,4,6)]
        C['T'] = [(0,7,4,7),(2,7,2,0)]
        C['U'] = [(0,7,0,1),(0,1,1,0),(1,0,3,0),(3,0,4,1),(4,1,4,7)]
        C['V'] = [(0,7,2,0),(2,0,4,7)]
        C['W'] = [(0,7,1,0),(1,0,2,4),(2,4,3,0),(3,0,4,7)]
        C['X'] = [(0,0,4,7),(0,7,4,0)]
        C['Y'] = [(0,7,2,4),(2,4,4,7),(2,4,2,0)]
        C['Z'] = [(0,7,4,7),(4,7,0,0),(0,0,4,0)]
        C['0'] = [(1,0,0,1),(0,1,0,6),(0,6,1,7),(1,7,3,7),(3,7,4,6),(4,6,4,1),(4,1,3,0),(3,0,1,0),(0,1,4,6)]
        C['1'] = [(1,6,2,7),(2,7,2,0),(1,0,3,0)]
        C['2'] = [(0,6,1,7),(1,7,3,7),(3,7,4,6),(4,6,4,5),(4,5,0,0),(0,0,4,0)]
        C['3'] = [(0,6,1,7),(1,7,3,7),(3,7,4,6),(4,6,4,5),(4,5,3,4),(3,4,2,4),(3,4,4,3),(4,3,4,1),(4,1,3,0),(3,0,1,0),(1,0,0,1)]
        C['4'] = [(0,7,0,4),(0,4,4,4),(3,7,3,0)]
        C['5'] = [(4,7,0,7),(0,7,0,4),(0,4,3,4),(3,4,4,3),(4,3,4,1),(4,1,3,0),(3,0,1,0),(1,0,0,1)]
        C['6'] = [(3,7,1,7),(1,7,0,6),(0,6,0,1),(0,1,1,0),(1,0,3,0),(3,0,4,1),(4,1,4,3),(4,3,3,4),(3,4,0,4)]
        C['7'] = [(0,7,4,7),(4,7,1,0)]
        C['8'] = [(1,0,0,1),(0,1,0,3),(0,3,1,4),(1,4,0,5),(0,5,0,6),(0,6,1,7),(1,7,3,7),(3,7,4,6),(4,6,4,5),(4,5,3,4),(3,4,4,3),(4,3,4,1),(4,1,3,0),(3,0,1,0),(1,4,3,4)]
        C['9'] = [(4,4,1,4),(1,4,0,5),(0,5,0,6),(0,6,1,7),(1,7,3,7),(3,7,4,6),(4,6,4,1),(4,1,3,0),(3,0,1,0),(1,0,0,1)]
        C[' '] = []
        C['.'] = [(2,0,2,0.6)]
        C[','] = [(2,0.5,1.5,-0.3)]
        C[':'] = [(2,1,2,1.8),(2,5,2,5.8)]
        C['!'] = [(2,2,2,2.7),(2,4,2,7)]
        C['?'] = [(0,6,1,7),(1,7,3,7),(3,7,4,6),(4,6,4,5),(4,5,3,4),(3,4,2,4),(2,4,2,3),(2,0.5,2,1.5)]
        C['-'] = [(1,4,3,4)]
        C['_'] = [(0,0,4,0)]
        C['/'] = [(0,0,4,7)]
        C['\\'] = [(0,7,4,0)]
        C['('] = [(2.5,0,1.5,1),(1.5,1,1.5,6),(1.5,6,2.5,7)]
        C[')'] = [(1.5,0,2.5,1),(2.5,1,2.5,6),(2.5,6,1.5,7)]
        C['['] = [(3,0,1,0),(1,0,1,7),(1,7,3,7)]
        C[']'] = [(1,0,3,0),(3,0,3,7),(3,7,1,7)]
        C['+'] = [(2,2,2,6),(0,4,4,4)]
        C['='] = [(0,3,4,3),(0,5,4,5)]
        C['<'] = [(3.5,7,0.5,4),(0.5,4,3.5,0)]
        C['>'] = [(0.5,7,3.5,4),(3.5,4,0.5,0)]
        C[';'] = [(2,5,2,5.8),(2,1.5,1.5,0.5)]
        cls._CHARS = C

    @classmethod
    def draw_text(cls, x, y, text, scale=1.0, color=(1.0, 1.0, 1.0)):
        cls._init()
        glColor3f(*color)
        glLineWidth(max(1.0, scale * 0.8))
        glBegin(GL_LINES)
        cx = x
        upper = text.upper()
        cw = 5 * scale
        spacing = 1.8 * scale
        for ch in upper:
            segs = cls._CHARS.get(ch)
            if segs:
                for x1, y1, x2, y2 in segs:
                    glVertex2f(cx + x1 * scale, y + y1 * scale)
                    glVertex2f(cx + x2 * scale, y + y2 * scale)
            cx += cw + spacing
        glEnd()

    @classmethod
    def text_width(cls, text, scale=1.0):
        cw = 5 * scale
        spacing = 1.8 * scale
        if not text:
            return 0
        return len(text) * (cw + spacing) - spacing


# ========================== WORLD ==========================

class Chunk:
    def __init__(self, cx, cz):
        self.cx = cx
        self.cz = cz
        self.blocks = np.zeros((CHUNK_SIZE, CHUNK_HEIGHT, CHUNK_SIZE), dtype=np.int8)
        self.dirty = True
        self.generated = False

    def get_block(self, x, y, z):
        if 0 <= x < CHUNK_SIZE and 0 <= y < CHUNK_HEIGHT and 0 <= z < CHUNK_SIZE:
            return int(self.blocks[x, y, z])
        return BLOCK_AIR

    def set_block(self, x, y, z, block_type):
        if 0 <= x < CHUNK_SIZE and 0 <= y < CHUNK_HEIGHT and 0 <= z < CHUNK_SIZE:
            self.blocks[x, y, z] = block_type
            self.dirty = True

# ========================== TEXTURE PACKS ==========================

# Standard block name mapping for texture packs
BLOCK_TEXTURE_NAMES = {
    BLOCK_GRASS: {'top': 'grass_top', 'bottom': 'dirt', 'side': 'grass_side'},
    BLOCK_DIRT: {'all': 'dirt'},
    BLOCK_STONE: {'all': 'stone'},
    BLOCK_WOOD: {'top': 'log_oak_top', 'bottom': 'log_oak_top', 'side': 'log_oak'},
    BLOCK_LEAVES: {'all': 'leaves_oak'},
    BLOCK_SAND: {'all': 'sand'},
    BLOCK_WATER: {'all': 'water_still'},
    BLOCK_COBBLESTONE: {'all': 'cobblestone'},
    BLOCK_PLANKS: {'all': 'planks_oak'},
    BLOCK_BEDROCK: {'all': 'bedrock'},
    BLOCK_COAL_ORE: {'all': 'coal_ore'},
    BLOCK_IRON_ORE: {'all': 'iron_ore'},
    BLOCK_GLASS: {'all': 'glass'},
    BLOCK_BRICK: {'all': 'brick'},
    BLOCK_SNOW: {'all': 'snow'},
}


class TexturePack:
    """Loads block textures from PNG files or generates procedural fallbacks."""

    def __init__(self, pack_path=None):
        self.pack_path = pack_path
        self.textures = {}  # block_id -> {'top': tex_id, 'side': tex_id, 'bottom': tex_id}
        self.atlas_texture = None
        self.enabled = HAS_PIL and pack_path is not None

    def load(self):
        """Load textures from disk, or generate procedural ones."""
        if not HAS_PIL:
            print("PIL not installed - using color-only rendering")
            return False

        for block_id, faces in BLOCK_TEXTURE_NAMES.items():
            self.textures[block_id] = {}
            for face_type, tex_name in faces.items():
                tex_id = self._load_texture(tex_name, block_id)
                self.textures[block_id][face_type] = tex_id
        return True

    def _load_texture(self, name, block_id):
        """Load a single texture PNG or generate procedural."""
        # Try to load from pack
        if self.pack_path:
            for subfolder in ['blocks', 'block', '']:
                for ext in ['.png', '.PNG']:
                    path = os.path.join(self.pack_path, subfolder, name + ext)
                    if os.path.isfile(path):
                        try:
                            return self._png_to_gl(path)
                        except Exception as e:
                            print("Failed to load " + path + ": " + str(e))
        
        # Generate procedural texture
        return self._generate_procedural(block_id, name)

    def _png_to_gl(self, path):
        """Convert PNG file to OpenGL texture."""
        img = Image.open(path).convert('RGBA')
        # Resize to 16x16 if bigger (support HD packs by downscaling)
        if img.size[0] > 64:
            img = img.resize((16, 16), Image.NEAREST)
        data = np.array(img, dtype=np.uint8)
        return self._upload_texture(data)

    def _generate_procedural(self, block_id, name):
        """Generate a 16x16 procedural texture using noise."""
        size = 16
        data = np.zeros((size, size, 4), dtype=np.uint8)
        base = BLOCK_COLORS.get(block_id, (0.5, 0.5, 0.5))
        r, g, b = int(base[0] * 255), int(base[1] * 255), int(base[2] * 255)

        rng = random.Random(block_id * 1337 + hash(name))

        for y in range(size):
            for x in range(size):
                # Add noise variation
                var = rng.randint(-25, 25)
                # Different patterns per block
                if block_id == BLOCK_WOOD and 'side' in name:
                    # Wood grain
                    if x % 4 == 0:
                        var -= 30
                elif block_id == BLOCK_BRICK:
                    # Brick pattern
                    if y % 4 == 0 or (x % 8 == 0 and (y // 4) % 2 == 0) or ((x + 4) % 8 == 0 and (y // 4) % 2 == 1):
                        var -= 40
                elif block_id == BLOCK_LEAVES:
                    # Random gaps
                    if rng.random() < 0.15:
                        data[y, x] = [0, 0, 0, 0]
                        continue
                elif block_id == BLOCK_GLASS:
                    # Mostly transparent with edges
                    if 1 < x < 14 and 1 < y < 14:
                        data[y, x] = [200, 220, 240, 50]
                        continue

                nr = max(0, min(255, r + var))
                ng = max(0, min(255, g + var))
                nb = max(0, min(255, b + var))
                data[y, x] = [nr, ng, nb, 255]

        return self._upload_texture(data)

    def _upload_texture(self, data):
        """Upload pixel data to OpenGL and return texture ID."""
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        h, w = data.shape[:2]
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, data.tobytes())
        glBindTexture(GL_TEXTURE_2D, 0)
        return tex_id

    def get_texture(self, block_id, face):
        """Get texture ID for a block face."""
        if block_id not in self.textures:
            return None
        faces = self.textures[block_id]
        if 'all' in faces:
            return faces['all']
        if face == 'top' and 'top' in faces:
            return faces['top']
        if face == 'bottom' and 'bottom' in faces:
            return faces['bottom']
        return faces.get('side', faces.get('top'))

    def cleanup(self):
        for block_faces in self.textures.values():
            for tex_id in block_faces.values():
                if tex_id:
                    glDeleteTextures([tex_id])
        self.textures.clear()

    @staticmethod
    def list_packs():
        """List all installed texture packs."""
        packs = ['[Procedural]']  # Default option
        if os.path.exists(TEXTUREPACKS_DIR):
            for name in sorted(os.listdir(TEXTUREPACKS_DIR)):
                full = os.path.join(TEXTUREPACKS_DIR, name)
                if os.path.isdir(full):
                    packs.append(name)
        return packs


class WorldGenerator:
    def __init__(self, seed=None):
        self.seed = seed if seed is not None else random.randint(0, 999_999_999)
        self.continentalness = PerlinNoise(self.seed)
        self.erosion = PerlinNoise(self.seed + 1)
        self.peaks = PerlinNoise(self.seed + 2)
        self.cave_noise = PerlinNoise(self.seed + 3)
        self.ore_noise = PerlinNoise(self.seed + 4)
        self.biome_noise = PerlinNoise(self.seed + 5)
        self.detail_noise = PerlinNoise(self.seed + 6)

    def get_height(self, wx, wz):
        c = self.continentalness.octave2d(wx * 0.002, wz * 0.002, octaves=5, persistence=0.45)
        e = self.erosion.octave2d(wx * 0.004, wz * 0.004, octaves=4, persistence=0.5)
        p = self.peaks.octave2d(wx * 0.01, wz * 0.01, octaves=4, persistence=0.55)
        d = self.detail_noise.octave2d(wx * 0.05, wz * 0.05, octaves=2, persistence=0.6)
        base = 28.0
        h = base + c * 18.0 + e * 8.0 * (0.5 + abs(c)) + p * 6.0 + d * 2.0
        return max(2, min(CHUNK_HEIGHT - 6, int(h)))

    def get_biome(self, wx, wz):
        t = self.biome_noise.octave2d(wx * 0.003, wz * 0.003, octaves=3, persistence=0.4)
        m = self.biome_noise.octave2d(wx * 0.003 + 500, wz * 0.003 + 500, octaves=3, persistence=0.4)
        if t > 0.3:
            return 4
        if t > 0.05 and m > 0.1:
            return 3
        if t < -0.25:
            return 1
        if m < -0.1:
            return 2
        return 0

    def generate_chunk(self, chunk):
        cx, cz = chunk.cx, chunk.cz
        for x in range(CHUNK_SIZE):
            for z in range(CHUNK_SIZE):
                wx = cx * CHUNK_SIZE + x
                wz = cz * CHUNK_SIZE + z
                height = self.get_height(wx, wz)
                biome = self.get_biome(wx, wz)
                for y in range(CHUNK_HEIGHT):
                    if y == 0:
                        chunk.blocks[x, y, z] = BLOCK_BEDROCK
                    elif y <= 3:
                        r = self.ore_noise.noise3d(wx * 0.5, y * 0.5, wz * 0.5)
                        chunk.blocks[x, y, z] = BLOCK_BEDROCK if r > -0.3 else BLOCK_STONE
                    elif y < height - 4:
                        cave = self.cave_noise.octave3d(wx * 0.06, y * 0.08, wz * 0.06, octaves=2)
                        if cave > 0.55:
                            chunk.blocks[x, y, z] = BLOCK_AIR
                        else:
                            ore = self.ore_noise.noise3d(wx * 0.12, y * 0.12, wz * 0.12)
                            if ore > 0.65 and y < 24:
                                chunk.blocks[x, y, z] = BLOCK_IRON_ORE
                            elif ore > 0.55 and y < 40:
                                chunk.blocks[x, y, z] = BLOCK_COAL_ORE
                            else:
                                chunk.blocks[x, y, z] = BLOCK_STONE
                    elif y < height - 1:
                        if biome == 1:
                            chunk.blocks[x, y, z] = BLOCK_SAND
                        else:
                            chunk.blocks[x, y, z] = BLOCK_DIRT
                    elif y < height:
                        if biome == 1:
                            chunk.blocks[x, y, z] = BLOCK_SAND
                        elif biome == 4:
                            chunk.blocks[x, y, z] = BLOCK_SNOW
                        elif height <= WATER_LEVEL + 2:
                            chunk.blocks[x, y, z] = BLOCK_SAND
                        else:
                            chunk.blocks[x, y, z] = BLOCK_GRASS
                    elif y <= WATER_LEVEL:
                        chunk.blocks[x, y, z] = BLOCK_WATER
        self._generate_trees(chunk)
        chunk.generated = True
        chunk.dirty = True

    def _generate_trees(self, chunk):
        rng = random.Random(self.seed + chunk.cx * 7919 + chunk.cz * 6271)
        for _ in range(rng.randint(0, 5)):
            tx = rng.randint(2, CHUNK_SIZE - 3)
            tz = rng.randint(2, CHUNK_SIZE - 3)
            wx = chunk.cx * CHUNK_SIZE + tx
            wz = chunk.cz * CHUNK_SIZE + tz
            biome = self.get_biome(wx, wz)
            if biome == 1:
                continue
            ground = self.get_height(wx, wz)
            if ground <= WATER_LEVEL + 1 or ground >= CHUNK_HEIGHT - 10:
                continue
            surface = chunk.get_block(tx, ground - 1, tz)
            if surface not in (BLOCK_GRASS, BLOCK_SNOW):
                continue
            trunk_h = rng.randint(4, 6)
            if biome == 2:
                trunk_h = rng.randint(5, 8)
            for y in range(ground, min(ground + trunk_h, CHUNK_HEIGHT)):
                chunk.set_block(tx, y, tz, BLOCK_WOOD)
            leaf_base = ground + trunk_h - 2
            leaf_top = ground + trunk_h + 1
            for ly in range(leaf_base, min(leaf_top + 1, CHUNK_HEIGHT)):
                radius = 2 if ly < leaf_top else 1
                for lx in range(-radius, radius + 1):
                    for lz in range(-radius, radius + 1):
                        if abs(lx) == radius and abs(lz) == radius and rng.random() > 0.5:
                            continue
                        if lx == 0 and lz == 0 and ly < ground + trunk_h:
                            continue
                        nx, nz = tx + lx, tz + lz
                        if 0 <= nx < CHUNK_SIZE and 0 <= nz < CHUNK_SIZE:
                            if chunk.get_block(nx, ly, nz) == BLOCK_AIR:
                                chunk.set_block(nx, ly, nz, BLOCK_LEAVES)


class World:
    def __init__(self, name, seed=None):
        self.name = name
        self.chunks = {}
        self.generator = WorldGenerator(seed)
        self.save_path = os.path.join(SAVES_DIR, name)
        os.makedirs(self.save_path, exist_ok=True)
        self.texture_pack = None

    def get_chunk(self, cx, cz):
        key = (cx, cz)
        if key not in self.chunks:
            chunk = Chunk(cx, cz)
            if not self._load_chunk(chunk):
                self.generator.generate_chunk(chunk)
            self.chunks[key] = chunk
        return self.chunks[key]

    def get_block(self, x, y, z):
        if y < 0 or y >= CHUNK_HEIGHT:
            return BLOCK_AIR
        cx = int(math.floor(x / CHUNK_SIZE))
        cz = int(math.floor(z / CHUNK_SIZE))
        lx = x - cx * CHUNK_SIZE
        lz = z - cz * CHUNK_SIZE
        key = (cx, cz)
        if key in self.chunks:
            return self.chunks[key].get_block(lx, y, lz)
        return BLOCK_AIR

    def set_block(self, x, y, z, block_type):
        if y < 0 or y >= CHUNK_HEIGHT:
            return
        cx = int(math.floor(x / CHUNK_SIZE))
        cz = int(math.floor(z / CHUNK_SIZE))
        lx = x - cx * CHUNK_SIZE
        lz = z - cz * CHUNK_SIZE
        key = (cx, cz)
        if key in self.chunks:
            self.chunks[key].set_block(lx, y, lz, block_type)
            if lx == 0 and (cx - 1, cz) in self.chunks:
                self.chunks[(cx - 1, cz)].dirty = True
            if lx == CHUNK_SIZE - 1 and (cx + 1, cz) in self.chunks:
                self.chunks[(cx + 1, cz)].dirty = True
            if lz == 0 and (cx, cz - 1) in self.chunks:
                self.chunks[(cx, cz - 1)].dirty = True
            if lz == CHUNK_SIZE - 1 and (cx, cz + 1) in self.chunks:
                self.chunks[(cx, cz + 1)].dirty = True

    def save(self, player_pos, player_rot):
        meta = {
            'name': self.name,
            'seed': self.generator.seed,
            'player_pos': list(player_pos),
            'player_rot': list(player_rot),
            'save_time': time.time()
        }
        with open(os.path.join(self.save_path, 'world.json'), 'w') as f:
            json.dump(meta, f, indent=2)
        for key, chunk in self.chunks.items():
            self._save_chunk(chunk)

    def _save_chunk(self, chunk):
        fp = os.path.join(self.save_path, "c." + str(chunk.cx) + "." + str(chunk.cz) + ".dat")
        with open(fp, 'wb') as f:
            np.save(f, chunk.blocks)

    def _load_chunk(self, chunk):
        fp = os.path.join(self.save_path, "c." + str(chunk.cx) + "." + str(chunk.cz) + ".dat")
        if os.path.exists(fp):
            try:
                with open(fp, 'rb') as f:
                    chunk.blocks = np.load(f)
                chunk.generated = True
                chunk.dirty = True
                return True
            except Exception:
                pass
        return False

    @staticmethod
    def load_world(name):
        sp = os.path.join(SAVES_DIR, name)
        mp = os.path.join(sp, 'world.json')
        if os.path.exists(mp):
            try:
                with open(mp, 'r') as f:
                    meta = json.load(f)
                w = World(name, meta.get('seed'))
                return w, meta.get('player_pos', [8, 40, 8]), meta.get('player_rot', [0, 0])
            except Exception:
                pass
        return None, None, None

    @staticmethod
    def list_worlds():
        worlds = []
        if os.path.exists(SAVES_DIR):
            for name in sorted(os.listdir(SAVES_DIR)):
                mp = os.path.join(SAVES_DIR, name, 'world.json')
                if os.path.exists(mp):
                    try:
                        with open(mp, 'r') as f:
                            meta = json.load(f)
                        worlds.append(meta)
                    except Exception:
                        worlds.append({'name': name})
        return worlds

    @staticmethod
    def delete_world(name):
        import shutil
        sp = os.path.join(SAVES_DIR, name)
        if os.path.exists(sp):
            shutil.rmtree(sp)


# ========================== MESH BUILDER ==========================

class MeshBuilder:
    FACES = {
        'top':    ( 0, 1, 0, [(-0.5, 0.5, 0.5),( 0.5, 0.5, 0.5),( 0.5, 0.5,-0.5),(-0.5, 0.5,-0.5)], ( 0, 1, 0)),
        'bottom': ( 0,-1, 0, [(-0.5,-0.5,-0.5),( 0.5,-0.5,-0.5),( 0.5,-0.5, 0.5),(-0.5,-0.5, 0.5)], ( 0,-1, 0)),
        'front':  ( 0, 0, 1, [(-0.5,-0.5, 0.5),( 0.5,-0.5, 0.5),( 0.5, 0.5, 0.5),(-0.5, 0.5, 0.5)], ( 0, 0, 1)),
        'back':   ( 0, 0,-1, [( 0.5,-0.5,-0.5),(-0.5,-0.5,-0.5),(-0.5, 0.5,-0.5),( 0.5, 0.5,-0.5)], ( 0, 0,-1)),
        'right':  ( 1, 0, 0, [( 0.5,-0.5, 0.5),( 0.5,-0.5,-0.5),( 0.5, 0.5,-0.5),( 0.5, 0.5, 0.5)], ( 1, 0, 0)),
        'left':   (-1, 0, 0, [(-0.5,-0.5,-0.5),(-0.5,-0.5, 0.5),(-0.5, 0.5, 0.5),(-0.5, 0.5,-0.5)], (-1, 0, 0)),
    }
    FACE_LIGHT = {'top': 1.0, 'bottom': 0.5, 'front': 0.8, 'back': 0.7, 'right': 0.75, 'left': 0.65}
    FACE_UV = [(0, 0), (1, 0), (1, 1), (0, 1)]  # UV coords for each vertex

    @staticmethod
    def build_chunk_mesh(world, chunk):
        """Returns dict: {texture_id: (vertices, colors, normals, uvs)}"""
        # Group triangles by texture
        by_texture = {}  # tex_id -> {'v': [], 'c': [], 'n': [], 'uv': []}
        cx_off = chunk.cx * CHUNK_SIZE
        cz_off = chunk.cz * CHUNK_SIZE

        def get_tex_face_type(fname):
            if fname == 'top': return 'top'
            if fname == 'bottom': return 'bottom'
            return 'side'

        for x in range(CHUNK_SIZE):
            for y in range(CHUNK_HEIGHT):
                for z in range(CHUNK_SIZE):
                    block = int(chunk.blocks[x, y, z])
                    if block == BLOCK_AIR:
                        continue
                    wx = cx_off + x
                    wz = cz_off + z
                    base_color = BLOCK_COLORS.get(block, (1, 0, 1))

                    for fname, (dx, dy, dz, fverts, normal) in MeshBuilder.FACES.items():
                        nx_, ny_, nz_ = x + dx, y + dy, z + dz
                        if 0 <= nx_ < CHUNK_SIZE and 0 <= ny_ < CHUNK_HEIGHT and 0 <= nz_ < CHUNK_SIZE:
                            nb = int(chunk.blocks[nx_, ny_, nz_])
                        else:
                            nb = world.get_block(wx + dx, ny_, wz + dz)

                        if block == BLOCK_WATER:
                            if nb == BLOCK_WATER:
                                continue
                            if nb != BLOCK_AIR and nb != BLOCK_GLASS:
                                continue
                        else:
                            if nb not in TRANSPARENT_BLOCKS:
                                continue
                            if nb == block and block == BLOCK_LEAVES:
                                continue

                        # Get texture for this face
                        tex_id = 0
                        if world.texture_pack:
                            tex_id = world.texture_pack.get_texture(block, get_tex_face_type(fname)) or 0

                        light = MeshBuilder.FACE_LIGHT[fname]
                        fc = base_color
                        if block == BLOCK_GRASS and tex_id == 0:
                            if fname == 'top':
                                fc = (0.30, 0.78, 0.22)
                            elif fname == 'bottom':
                                fc = (0.55, 0.36, 0.16)
                            else:
                                fc = (0.40, 0.55, 0.20)

                        # If we have a texture, use white color (so texture shows properly)
                        if tex_id:
                            color = (light, light, light)
                        else:
                            color = (fc[0] * light, fc[1] * light, fc[2] * light)

                        if tex_id not in by_texture:
                            by_texture[tex_id] = {'v': [], 'c': [], 'n': [], 'uv': []}
                        bucket = by_texture[tex_id]

                        for idx in (0, 1, 2, 0, 2, 3):
                            vx, vy, vz = fverts[idx]
                            u, v = MeshBuilder.FACE_UV[idx]
                            bucket['v'].extend((wx + vx + 0.5, y + vy + 0.5, wz + vz + 0.5))
                            bucket['c'].extend(color)
                            bucket['n'].extend(normal)
                            bucket['uv'].extend((u, v))

        # Convert to numpy arrays
        result = {}
        for tex_id, data in by_texture.items():
            result[tex_id] = (
                np.array(data['v'], dtype=np.float32),
                np.array(data['c'], dtype=np.float32),
                np.array(data['n'], dtype=np.float32),
                np.array(data['uv'], dtype=np.float32),
            )
        return result

class ChunkRenderer:
    def __init__(self):
        self.vbos = {}  # (cx,cz) -> {tex_id: (vbo_v, vbo_c, vbo_n, vbo_uv, count)}

    def update_chunk(self, world, chunk):
        key = (chunk.cx, chunk.cz)
        meshes = MeshBuilder.build_chunk_mesh(world, chunk)
        self._delete(key)
        
        if not meshes:
            chunk.dirty = False
            return
        
        self.vbos[key] = {}
        for tex_id, (v, c, n, uv) in meshes.items():
            vbo_v = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, vbo_v)
            glBufferData(GL_ARRAY_BUFFER, v.nbytes, v, GL_STATIC_DRAW)
            vbo_c = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, vbo_c)
            glBufferData(GL_ARRAY_BUFFER, c.nbytes, c, GL_STATIC_DRAW)
            vbo_n = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, vbo_n)
            glBufferData(GL_ARRAY_BUFFER, n.nbytes, n, GL_STATIC_DRAW)
            vbo_uv = glGenBuffers(1)
            glBindBuffer(GL_ARRAY_BUFFER, vbo_uv)
            glBufferData(GL_ARRAY_BUFFER, uv.nbytes, uv, GL_STATIC_DRAW)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            self.vbos[key][tex_id] = (vbo_v, vbo_c, vbo_n, vbo_uv, len(v) // 3)
        chunk.dirty = False

    def render_chunk(self, key):
        entries = self.vbos.get(key)
        if not entries:
            return
        
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        glEnableClientState(GL_NORMAL_ARRAY)
        
        for tex_id, (vbo_v, vbo_c, vbo_n, vbo_uv, count) in entries.items():
            if tex_id:
                glEnable(GL_TEXTURE_2D)
                glBindTexture(GL_TEXTURE_2D, tex_id)
                glEnableClientState(GL_TEXTURE_COORD_ARRAY)
                glBindBuffer(GL_ARRAY_BUFFER, vbo_uv)
                glTexCoordPointer(2, GL_FLOAT, 0, None)
            else:
                glDisable(GL_TEXTURE_2D)
            
            glBindBuffer(GL_ARRAY_BUFFER, vbo_v)
            glVertexPointer(3, GL_FLOAT, 0, None)
            glBindBuffer(GL_ARRAY_BUFFER, vbo_c)
            glColorPointer(3, GL_FLOAT, 0, None)
            glBindBuffer(GL_ARRAY_BUFFER, vbo_n)
            glNormalPointer(GL_FLOAT, 0, None)
            
            glDrawArrays(GL_TRIANGLES, 0, count)
            
            if tex_id:
                glDisableClientState(GL_TEXTURE_COORD_ARRAY)
        
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glDisable(GL_TEXTURE_2D)
        glDisableClientState(GL_VERTEX_ARRAY)
        glDisableClientState(GL_COLOR_ARRAY)
        glDisableClientState(GL_NORMAL_ARRAY)

    def _delete(self, key):
        entries = self.vbos.pop(key, None)
        if entries:
            for tex_id, (vbo_v, vbo_c, vbo_n, vbo_uv, _) in entries.items():
                glDeleteBuffers(4, [vbo_v, vbo_c, vbo_n, vbo_uv])

    def cleanup(self):
        for k in list(self.vbos):
            self._delete(k)


# ========================== PLAYER ==========================

class Player:
    def __init__(self, x=8, y=40, z=8):
        self.x, self.y, self.z = float(x), float(y), float(z)
        self.vy = 0.0
        self.yaw = 0.0
        self.pitch = 0.0
        self.on_ground = False
        self.flying = False
        self.inventory = [
            BLOCK_COBBLESTONE, BLOCK_DIRT, BLOCK_GRASS, BLOCK_WOOD,
            BLOCK_PLANKS, BLOCK_STONE, BLOCK_SAND, BLOCK_GLASS, BLOCK_BRICK
        ]
        self.selected_slot = 0
        self.selected_block = self.inventory[0]

    def pos(self):
        return [self.x, self.y, self.z]

    def rot(self):
        return [self.yaw, self.pitch]

    def look_vec(self):
        cp = math.cos(self.pitch)
        return (math.sin(self.yaw) * cp, math.sin(self.pitch), -math.cos(self.yaw) * cp)

    def update(self, dt, world, keys):
        fwd = 0
        strafe = 0
        if keys.get(glfw.KEY_W):
            fwd += 1
        if keys.get(glfw.KEY_S):
            fwd -= 1
        if keys.get(glfw.KEY_A):
            strafe -= 1
        if keys.get(glfw.KEY_D):
            strafe += 1
        speed = PLAYER_SPEED
        if keys.get(glfw.KEY_LEFT_SHIFT):
            speed *= 1.6
        mx = math.sin(self.yaw) * fwd + math.cos(self.yaw) * strafe
        mz = -math.cos(self.yaw) * fwd + math.sin(self.yaw) * strafe
        ln = math.sqrt(mx * mx + mz * mz)
        if ln > 0:
            mx /= ln
            mz /= ln
        if self.flying:
            self.x += mx * speed * dt
            self.z += mz * speed * dt
            if keys.get(glfw.KEY_SPACE):
                self.y += speed * dt
            if keys.get(glfw.KEY_LEFT_CONTROL):
                self.y -= speed * dt
            self.vy = 0
        else:
            self.vy += GRAVITY * dt
            if keys.get(glfw.KEY_SPACE) and self.on_ground:
                self.vy = JUMP_SPEED
                self.on_ground = False
            nx = self.x + mx * speed * dt
            ny = self.y + self.vy * dt
            nz = self.z + mz * speed * dt
            if not self._collides(world, nx, self.y, self.z):
                self.x = nx
            if not self._collides(world, self.x, self.y, nz):
                self.z = nz
            if not self._collides(world, self.x, ny, self.z):
                self.y = ny
                self.on_ground = False
            else:
                if self.vy < 0:
                    self.on_ground = True
                    self.y = math.floor(self.y) + 0.001
                self.vy = 0
        if self.y < 1:
            self.y = 1
            self.vy = 0
            self.on_ground = True

    def _collides(self, world, x, y, z):
        pad = 0.25
        for dx in (-pad, pad):
            for dz in (-pad, pad):
                for dy in (0, 0.9, PLAYER_HEIGHT - 0.1):
                    bx = int(math.floor(x + dx))
                    by = int(math.floor(y + dy))
                    bz = int(math.floor(z + dz))
                    b = world.get_block(bx, by, bz)
                    if b != BLOCK_AIR and b != BLOCK_WATER:
                        return True
        return False

    def raycast(self, world):
        dx, dy, dz = self.look_vec()
        ey = self.y + PLAYER_HEIGHT - 0.2
        px, py, pz = self.x, ey, self.z
        step = 0.04
        prev = None
        for _ in range(int(REACH_DISTANCE / step)):
            bx = int(math.floor(px))
            by = int(math.floor(py))
            bz = int(math.floor(pz))
            b = world.get_block(bx, by, bz)
            if b != BLOCK_AIR and b != BLOCK_WATER:
                return (bx, by, bz), prev
            prev = (bx, by, bz)
            px += dx * step
            py += dy * step
            pz += dz * step
        return None, None


# ========================== GAME STATES ==========================

ST_LOGIN = 0
ST_MAIN = 1
ST_WORLDS = 2
ST_CREATE = 3
ST_PLAYING = 4
ST_PAUSE = 5


# ========================== GAME ==========================

class Game:
    def __init__(self):
        self.W = 960
        self.H = 540
        self.window = None
        self.state = ST_LOGIN
        self.acct = AccountManager()
        self.keys = {}
        self.mouse_captured = False
        self.last_mx = 0
        self.last_my = 0
        self.lclick = False
        self.rclick = False
        self.world = None
        self.player = None
        self.renderer = None
        self.ti1 = ""
        self.ti2 = ""
        self.active_field = 0
        self.ui_msg = ""
        self.ui_msg_t = 0.0
        self.wlist = []
        self.wsel = 0
        self.action_cd = 0.0
        self.lt = 0.0
        self.fps = 0
        self.fc = 0
        self.ft = 0.0

    def run(self):
        print("PyCraft starting...")
        if not glfw.init():
            print("GLFW init failed!")
            return
        print("GLFW initialized")
        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
        self.window = glfw.create_window(self.W, self.H, "PyCraft", None, None)
        if not self.window:
            print("Window creation failed!")
            glfw.terminate()
            return
        print("Window created")
        glfw.make_context_current(self.window)
        glfw.swap_interval(1)
        glfw.set_key_callback(self.window, self._on_key)
        glfw.set_mouse_button_callback(self.window, self._on_mbtn)
        glfw.set_scroll_callback(self.window, self._on_scroll)
        glfw.set_char_callback(self.window, self._on_char)
        glfw.set_framebuffer_size_callback(self.window, self._on_resize)
        self._init_gl()
        self.renderer = ChunkRenderer()
        
        # Load texture pack
        self.texture_pack = None
        pack_names = TexturePack.list_packs()
        # Use first non-procedural pack if available, else procedural
        selected_pack = None
        for p in pack_names:
            if p != '[Procedural]':
                selected_pack = p
                break
        
        if selected_pack:
            pack_path = os.path.join(TEXTUREPACKS_DIR, selected_pack)
            print("Loading texture pack: " + selected_pack)
        else:
            pack_path = None
            print("No texture pack found - generating procedural textures")
        
        self.texture_pack = TexturePack(pack_path)
        if self.texture_pack.load():
            print("Textures loaded successfully")
        else:
            print("Failed to load textures")
            self.texture_pack = None
        if self.acct.auto_login():
            self.state = ST_MAIN
        self.lt = time.time()
        print("Entering main loop")
        while not glfw.window_should_close(self.window):
            frame_start = time.time()
            now = time.time()
            dt = min(now - self.lt, 0.1)
            self.lt = now
            self.fc += 1
            self.ft += dt
            if self.ft >= 1.0:
                self.fps = self.fc
                self.fc = 0
                self.ft = 0.0
            glfw.poll_events()
            self._update(dt)
            self._render()
            glfw.swap_buffers(self.window)
            self.lclick = False
            self.rclick = False
            elapsed = time.time() - frame_start
            sleep_time = FRAME_TIME - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)
        self._cleanup()
        glfw.terminate()

    def _init_gl(self):
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)
        glCullFace(GL_BACK)
        glEnable(GL_FOG)
        glFogfv(GL_FOG_COLOR, [0.58, 0.78, 0.98, 1.0])
        glFogi(GL_FOG_MODE, GL_LINEAR)
        glFogf(GL_FOG_START, CHUNK_SIZE * (RENDER_DISTANCE - 1.5))
        glFogf(GL_FOG_END, CHUNK_SIZE * RENDER_DISTANCE)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)
        glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
        glLightfv(GL_LIGHT0, GL_POSITION, [0.4, 1.0, 0.3, 0.0])
        glLightfv(GL_LIGHT0, GL_AMBIENT, [0.35, 0.35, 0.4, 1.0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE, [0.9, 0.88, 0.82, 1.0])

    def _on_key(self, win, key, sc, action, mods):
        if action == glfw.PRESS:
            self.keys[key] = True
        elif action == glfw.RELEASE:
            self.keys[key] = False
        if action != glfw.PRESS:
            return
        if self.state in (ST_LOGIN, ST_CREATE):
            if key == glfw.KEY_TAB:
                self.active_field = 1 - self.active_field
            elif key == glfw.KEY_BACKSPACE:
                if self.active_field == 0 and self.ti1:
                    self.ti1 = self.ti1[:-1]
                elif self.active_field == 1 and self.ti2:
                    self.ti2 = self.ti2[:-1]
            elif key == glfw.KEY_ENTER:
                self._enter()
            elif key == glfw.KEY_ESCAPE:
                if self.state == ST_CREATE:
                    self.state = ST_WORLDS
                    self._clear_ti()
        elif self.state == ST_MAIN:
            if key == glfw.KEY_ESCAPE:
                glfw.set_window_should_close(win, True)
        elif self.state == ST_WORLDS:
            if key == glfw.KEY_ESCAPE:
                self.state = ST_MAIN
            elif key == glfw.KEY_UP and self.wlist:
                self.wsel = (self.wsel - 1) % len(self.wlist)
            elif key == glfw.KEY_DOWN and self.wlist:
                self.wsel = (self.wsel + 1) % len(self.wlist)
            elif key == glfw.KEY_ENTER:
                self._load_sel_world()
            elif key == glfw.KEY_DELETE:
                self._del_sel_world()
            elif key == glfw.KEY_N:
                self.state = ST_CREATE
                self._clear_ti()
        elif self.state == ST_PLAYING:
            if key == glfw.KEY_ESCAPE:
                self.state = ST_PAUSE
                self._release_mouse()
            elif key == glfw.KEY_F:
                self.player.flying = not self.player.flying
            else:
                for i in range(9):
                    if key == glfw.KEY_1 + i and i < len(self.player.inventory):
                        self.player.selected_slot = i
                        self.player.selected_block = self.player.inventory[i]
        elif self.state == ST_PAUSE:
            if key == glfw.KEY_ESCAPE:
                self.state = ST_PLAYING
                self._capture_mouse()
            elif key == glfw.KEY_Q:
                self._save_quit()

    def _on_char(self, win, cp):
        ch = chr(cp)
        if self.state in (ST_LOGIN, ST_CREATE):
            if self.active_field == 0:
                self.ti1 += ch
            else:
                self.ti2 += ch

    def _on_mbtn(self, win, btn, action, mods):
        if action != glfw.PRESS:
            return
        if self.state == ST_PLAYING:
            if not self.mouse_captured:
                self._capture_mouse()
                return
            if btn == glfw.MOUSE_BUTTON_LEFT:
                self.lclick = True
            elif btn == glfw.MOUSE_BUTTON_RIGHT:
                self.rclick = True
        else:
            mx, my = glfw.get_cursor_pos(win)
            self._menu_click(mx, my)

    def _on_scroll(self, win, xo, yo):
        if self.state == ST_PLAYING and self.player:
            self.player.selected_slot = (self.player.selected_slot - int(yo)) % len(self.player.inventory)
            self.player.selected_block = self.player.inventory[self.player.selected_slot]

    def _on_resize(self, win, w, h):
        self.W = max(w, 1)
        self.H = max(h, 1)
        glViewport(0, 0, self.W, self.H)

    def _capture_mouse(self):
        glfw.set_input_mode(self.window, glfw.CURSOR, glfw.CURSOR_DISABLED)
        self.mouse_captured = True
        self.last_mx, self.last_my = glfw.get_cursor_pos(self.window)

    def _release_mouse(self):
        glfw.set_input_mode(self.window, glfw.CURSOR, glfw.CURSOR_NORMAL)
        self.mouse_captured = False

    def _clear_ti(self):
        self.ti1 = ""
        self.ti2 = ""
        self.active_field = 0
        self.ui_msg = ""

    def _msg(self, s):
        self.ui_msg = s
        self.ui_msg_t = time.time()

    def _enter(self):
        if self.state == ST_LOGIN:
            ok, m = self.acct.login(self.ti1, self.ti2)
            if not ok:
                ok2, m2 = self.acct.create_account(self.ti1, self.ti2)
                if ok2:
                    self.acct.login(self.ti1, self.ti2)
                    self.state = ST_MAIN
                    self._clear_ti()
                    return
                self._msg(m)
            else:
                self.state = ST_MAIN
                self._clear_ti()
        elif self.state == ST_CREATE:
            name = self.ti1.strip()
            if not name:
                self._msg("Enter a world name")
                return
            seed = None
            if self.ti2.strip():
                try:
                    seed = int(self.ti2)
                except ValueError:
                    seed = hash(self.ti2) % 999_999_999
            self._start_sp(name, seed)
            self._clear_ti()

    def _load_sel_world(self):
        if not self.wlist:
            return
        if 0 <= self.wsel < len(self.wlist):
            name = self.wlist[self.wsel].get('name', '')
            w, pos, rot = World.load_world(name)
            if w:
                self.world = w
                self.player = Player(*pos)
                if rot:
                    self.player.yaw, self.player.pitch = rot
                self.state = ST_PLAYING
                self._capture_mouse()

    def _del_sel_world(self):
        if not self.wlist or not (0 <= self.wsel < len(self.wlist)):
            return
        World.delete_world(self.wlist[self.wsel]['name'])
        self.wlist = World.list_worlds()
        self.wsel = min(self.wsel, max(0, len(self.wlist) - 1))

    def _start_sp(self, name, seed=None):
        self.world = World(name, seed)
        sh = self.world.generator.get_height(8, 8) + 2
        self.player = Player(8, sh, 8)
        self.state = ST_PLAYING
        self._capture_mouse()

    def _save_quit(self):
        if self.world and self.player:
            self.world.save(self.player.pos(), self.player.rot())
        if self.renderer:
            self.renderer.cleanup()
        self.world = None
        self.player = None
        self.state = ST_MAIN
        self._release_mouse()

    def _menu_click(self, mx, my):
        sx = mx / self.W
        sy = 1.0 - my / self.H
        if self.state == ST_LOGIN:
            if 0.35 < sx < 0.65 and 0.25 < sy < 0.31:
                self._enter()
            elif 0.3 < sx < 0.7 and 0.52 < sy < 0.58:
                self.active_field = 0
            elif 0.3 < sx < 0.7 and 0.39 < sy < 0.45:
                self.active_field = 1
        elif self.state == ST_MAIN:
            if 0.35 < sx < 0.65 and 0.52 < sy < 0.58:
                self.wlist = World.list_worlds()
                self.state = ST_WORLDS
            elif 0.35 < sx < 0.65 and 0.42 < sy < 0.48:
                self.acct.logout()
                self.state = ST_LOGIN
                self._clear_ti()
            elif 0.35 < sx < 0.65 and 0.32 < sy < 0.38:
                glfw.set_window_should_close(self.window, True)
        elif self.state == ST_WORLDS:
            for i in range(len(self.wlist)):
                wy = 0.72 - i * 0.08
                if 0.12 < sx < 0.88 and wy - 0.03 < sy < wy + 0.03:
                    if self.wsel == i:
                        self._load_sel_world()
                    else:
                        self.wsel = i
            if 0.15 < sx < 0.35 and 0.07 < sy < 0.13:
                self._load_sel_world()
            elif 0.4 < sx < 0.6 and 0.07 < sy < 0.13:
                self.state = ST_CREATE
                self._clear_ti()
            elif 0.65 < sx < 0.85 and 0.07 < sy < 0.13:
                self._del_sel_world()
        elif self.state == ST_CREATE:
            if 0.35 < sx < 0.65 and 0.25 < sy < 0.31:
                self._enter()

    def _update(self, dt):
        if self.state != ST_PLAYING:
            return
        if not self.world or not self.player:
            return
        if self.mouse_captured:
            mx, my = glfw.get_cursor_pos(self.window)
            dx = mx - self.last_mx
            dy = my - self.last_my
            self.last_mx = mx
            self.last_my = my
            self.player.yaw += dx * MOUSE_SENSITIVITY
            self.player.pitch = max(-math.pi / 2 + 0.01, min(math.pi / 2 - 0.01, self.player.pitch - dy * MOUSE_SENSITIVITY))
        self.player.update(dt, self.world, self.keys)
        self.action_cd = max(0, self.action_cd - dt)
        if self.action_cd <= 0:
            if self.lclick:
                hit, _ = self.player.raycast(self.world)
                if hit:
                    bx, by, bz = hit
                    if self.world.get_block(bx, by, bz) != BLOCK_BEDROCK:
                        self.world.set_block(bx, by, bz, BLOCK_AIR)
                        self.action_cd = 0.2
            if self.rclick:
                hit, place = self.player.raycast(self.world)
                if hit and place and place[0] is not None:
                    px, py, pz = place
                    ok = True
                    for pdy in range(int(math.ceil(PLAYER_HEIGHT)) + 1):
                        if (int(math.floor(self.player.x)), int(math.floor(self.player.y + pdy)), int(math.floor(self.player.z))) == (px, py, pz):
                            ok = False
                            break
                    if ok:
                        self.world.set_block(px, py, pz, self.player.selected_block)
                        self.action_cd = 0.2
        pcx = int(math.floor(self.player.x / CHUNK_SIZE))
        pcz = int(math.floor(self.player.z / CHUNK_SIZE))
        built = 0
        for dx in range(-RENDER_DISTANCE, RENDER_DISTANCE + 1):
            for dz in range(-RENDER_DISTANCE, RENDER_DISTANCE + 1):
                chunk = self.world.get_chunk(pcx + dx, pcz + dz)
                if chunk.dirty and built < 2:
                    self.renderer.update_chunk(self.world, chunk)
                    built += 1
        for key in list(self.renderer.vbos):
            if abs(key[0] - pcx) > RENDER_DISTANCE + 1 or abs(key[1] - pcz) > RENDER_DISTANCE + 1:
                self.renderer._delete(key)

    def _render(self):
        if self.state in (ST_PLAYING, ST_PAUSE):
            glClearColor(0.58, 0.78, 0.98, 1.0)
        else:
            glClearColor(0.12, 0.12, 0.18, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        if self.state in (ST_PLAYING, ST_PAUSE):
            self._render_3d()
            self._render_hud()
            if self.state == ST_PAUSE:
                self._render_pause()
        else:
            self._render_menu()

    def _render_3d(self):
        if not self.world or not self.player:
            return
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(70, self.W / max(self.H, 1), 0.1, CHUNK_SIZE * (RENDER_DISTANCE + 1))
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        ey = self.player.y + PLAYER_HEIGHT - 0.2
        lx, ly, lz = self.player.look_vec()
        gluLookAt(self.player.x, ey, self.player.z,
                  self.player.x + lx, ey + ly, self.player.z + lz,
                  0, 1, 0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_FOG)
        glEnable(GL_CULL_FACE)
        pcx = int(math.floor(self.player.x / CHUNK_SIZE))
        pcz = int(math.floor(self.player.z / CHUNK_SIZE))
        for dx in range(-RENDER_DISTANCE, RENDER_DISTANCE + 1):
            for dz in range(-RENDER_DISTANCE, RENDER_DISTANCE + 1):
                self.renderer.render_chunk((pcx + dx, pcz + dz))
        self._draw_highlight()

    def _draw_highlight(self):
        if not self.player or not self.world:
            return
        hit, _ = self.player.raycast(self.world)
        if not hit:
            return
        bx, by, bz = hit
        glDisable(GL_LIGHTING)
        glDisable(GL_FOG)
        glDisable(GL_DEPTH_TEST)
        glLineWidth(2.5)
        glColor3f(0.1, 0.1, 0.1)
        edges = [
            (0,0,0,1,0,0),(0,0,0,0,1,0),(0,0,0,0,0,1),
            (1,0,0,1,1,0),(1,0,0,1,0,1),(0,1,0,1,1,0),
            (0,1,0,0,1,1),(0,0,1,1,0,1),(0,0,1,0,1,1),
            (1,1,0,1,1,1),(1,0,1,1,1,1),(0,1,1,1,1,1),
        ]
        glBegin(GL_LINES)
        for x1, y1, z1, x2, y2, z2 in edges:
            glVertex3f(bx + x1, by + y1, bz + z1)
            glVertex3f(bx + x2, by + y2, bz + z2)
        glEnd()
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_FOG)

    def _setup_2d(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.W, 0, self.H, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        glDisable(GL_FOG)
        glDisable(GL_CULL_FACE)

    def _render_hud(self):
        self._setup_2d()
        p = self.player
        cx, cy = self.W // 2, self.H // 2
        glColor3f(1, 1, 1)
        glLineWidth(2)
        glBegin(GL_LINES)
        glVertex2f(cx - 12, cy); glVertex2f(cx + 12, cy)
        glVertex2f(cx, cy - 12); glVertex2f(cx, cy + 12)
        glEnd()
        n = len(p.inventory)
        hw = n * 40
        hx = (self.W - hw) // 2
        hy = 10
        for i, b in enumerate(p.inventory):
            sx = hx + i * 40
            if i == p.selected_slot:
                glColor3f(1, 1, 1)
                glLineWidth(2)
                glBegin(GL_LINE_LOOP)
                glVertex2f(sx, hy); glVertex2f(sx + 36, hy)
                glVertex2f(sx + 36, hy + 36); glVertex2f(sx, hy + 36)
                glEnd()
            c = BLOCK_COLORS.get(b, (1, 0, 1))
            glColor3f(*c)
            self._quad(sx + 4, hy + 4, 28, 28)
        bn = BLOCK_NAMES.get(p.selected_block, "?")
        TextRenderer.draw_text((self.W - TextRenderer.text_width(bn, 1.5)) / 2, 58, bn, 1.5, (1, 1, 1))
        s = 1.2
        TextRenderer.draw_text(5, self.H - 15, "FPS: " + str(self.fps), s, (1, 1, 0.6))
        TextRenderer.draw_text(5, self.H - 30, "XYZ: " + str(round(p.x, 1)) + " " + str(round(p.y, 1)) + " " + str(round(p.z, 1)), s, (1, 1, 1))
        if p.flying:
            TextRenderer.draw_text(5, self.H - 45, "FLYING", s, (0.5, 1, 0.5))
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_CULL_FACE)

    def _render_pause(self):
        self._setup_2d()
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0, 0, 0, 0.6)
        self._quad(0, 0, self.W, self.H)
        glDisable(GL_BLEND)
        t = "GAME PAUSED"
        TextRenderer.draw_text((self.W - TextRenderer.text_width(t, 3.5)) / 2, self.H * 0.65, t, 3.5, (1, 1, 1))
        t2 = "ESC - RESUME"
        TextRenderer.draw_text((self.W - TextRenderer.text_width(t2, 1.8)) / 2, self.H * 0.48, t2, 1.8, (0.8, 0.8, 0.8))
        t3 = "Q - SAVE AND QUIT"
        TextRenderer.draw_text((self.W - TextRenderer.text_width(t3, 1.8)) / 2, self.H * 0.40, t3, 1.8, (0.8, 0.8, 0.8))
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_CULL_FACE)

    def _render_menu(self):
        self._setup_2d()
        if self.state == ST_LOGIN:
            self._draw_title("PYCRAFT", 5.5, (0.28, 0.92, 0.38))
            self._draw_subtitle("LOGIN OR CREATE ACCOUNT", (0.65, 0.65, 0.75))
            self._draw_field(0.5, 0.55, self.ti1, "USERNAME", self.active_field == 0)
            self._draw_field(0.5, 0.42, self.ti2, "PASSWORD", self.active_field == 1, True)
            self._draw_btn(0.5, 0.28, "LOGIN / REGISTER")
            self._draw_msg()
            self._draw_hint("ENTER: LOGIN  TAB: SWITCH FIELD")
        elif self.state == ST_MAIN:
            self._draw_title("PYCRAFT", 6.0, (0.28, 0.92, 0.38))
            u = self.acct.current_user or "Guest"
            TextRenderer.draw_text(10, self.H - 20, "LOGGED IN AS: " + u, 1.2, (0.6, 0.8, 0.6))
            self._draw_btn(0.5, 0.55, "PLAY")
            self._draw_btn(0.5, 0.45, "LOGOUT")
            self._draw_btn(0.5, 0.35, "QUIT")
        elif self.state == ST_WORLDS:
            self._draw_title("SELECT WORLD", 3.0, (1, 1, 1))
            if not self.wlist:
                m = "NO WORLDS - PRESS N OR NEW WORLD"
                TextRenderer.draw_text((self.W - TextRenderer.text_width(m, 1.5)) / 2, self.H * 0.5, m, 1.5, (0.6, 0.6, 0.7))
            else:
                for i, w in enumerate(self.wlist):
                    yp = self.H * (0.72 - i * 0.08)
                    name = w.get('name', '?')
                    if i == self.wsel:
                        glColor3f(0.22, 0.28, 0.42)
                        self._quad(self.W * 0.12, yp - 12, self.W * 0.76, 27)
                        col = (1, 1, 0.6)
                    else:
                        col = (0.8, 0.8, 0.8)
                    TextRenderer.draw_text(self.W * 0.14, yp, name, 1.3, col)
            self._draw_btn_small(0.25, 0.1, "PLAY")
            self._draw_btn_small(0.5, 0.1, "NEW WORLD")
            self._draw_btn_small(0.75, 0.1, "DELETE")
            self._draw_hint("UP/DOWN: SELECT  ENTER: PLAY  N: NEW  DEL: DELETE  ESC: BACK")
        elif self.state == ST_CREATE:
            self._draw_title("CREATE NEW WORLD", 3.0, (0.28, 0.92, 0.38))
            self._draw_field(0.5, 0.55, self.ti1, "WORLD NAME", self.active_field == 0)
            self._draw_field(0.5, 0.42, self.ti2, "SEED (OPTIONAL)", self.active_field == 1)
            self._draw_btn(0.5, 0.28, "CREATE")
            self._draw_msg()
            self._draw_hint("ENTER: CREATE  ESC: BACK")

    def _quad(self, x, y, w, h):
        glBegin(GL_QUADS)
        glVertex2f(x, y)
        glVertex2f(x + w, y)
        glVertex2f(x + w, y + h)
        glVertex2f(x, y + h)
        glEnd()

    def _draw_title(self, text, scale, color):
        tw = TextRenderer.text_width(text, scale)
        TextRenderer.draw_text((self.W - tw) / 2, self.H * 0.80, text, scale, color)

    def _draw_subtitle(self, text, color):
        tw = TextRenderer.text_width(text, 1.5)
        TextRenderer.draw_text((self.W - tw) / 2, self.H * 0.72, text, 1.5, color)

    def _draw_btn(self, bx, by, label):
        px = bx * self.W
        py = by * self.H
        bw = 0.32 * self.W
        bh = 0.06 * self.H
        glColor3f(0.22, 0.28, 0.38)
        self._quad(px - bw / 2, py - bh / 2, bw, bh)
        glColor3f(0.55, 0.65, 0.8)
        glLineWidth(1)
        glBegin(GL_LINE_LOOP)
        glVertex2f(px - bw / 2, py - bh / 2)
        glVertex2f(px + bw / 2, py - bh / 2)
        glVertex2f(px + bw / 2, py + bh / 2)
        glVertex2f(px - bw / 2, py + bh / 2)
        glEnd()
        tw = TextRenderer.text_width(label, 1.5)
        TextRenderer.draw_text(px - tw / 2, py - 5, label, 1.5, (1, 1, 1))

    def _draw_btn_small(self, bx, by, label):
        px = bx * self.W
        py = by * self.H
        bw = 0.2 * self.W
        bh = 0.05 * self.H
        glColor3f(0.22, 0.28, 0.38)
        self._quad(px - bw / 2, py - bh / 2, bw, bh)
        glColor3f(0.55, 0.65, 0.8)
        glLineWidth(1)
        glBegin(GL_LINE_LOOP)
        glVertex2f(px - bw / 2, py - bh / 2)
        glVertex2f(px + bw / 2, py - bh / 2)
        glVertex2f(px + bw / 2, py + bh / 2)
        glVertex2f(px - bw / 2, py + bh / 2)
        glEnd()
        tw = TextRenderer.text_width(label, 1.2)
        TextRenderer.draw_text(px - tw / 2, py - 4, label, 1.2, (1, 1, 1))

    def _draw_field(self, fx, fy, text, label, active, pw=False):
        px = fx * self.W
        py = fy * self.H
        fw = 0.42 * self.W
        fh = 0.06 * self.H
        TextRenderer.draw_text(px - fw / 2, py + fh / 2 + 6, label, 1.1, (0.6, 0.6, 0.75))
        if active:
            glColor3f(0.25, 0.25, 0.3)
        else:
            glColor3f(0.18, 0.18, 0.22)
        self._quad(px - fw / 2, py - fh / 2, fw, fh)
        c = (0.45, 0.75, 1.0) if active else (0.35, 0.35, 0.45)
        glColor3f(*c)
        glLineWidth(2 if active else 1)
        glBegin(GL_LINE_LOOP)
        glVertex2f(px - fw / 2, py - fh / 2)
        glVertex2f(px + fw / 2, py - fh / 2)
        glVertex2f(px + fw / 2, py + fh / 2)
        glVertex2f(px - fw / 2, py + fh / 2)
        glEnd()
        disp = '*' * len(text) if pw else text
        cur = "_" if active and int(time.time() * 2) % 2 == 0 else ""
        TextRenderer.draw_text(px - fw / 2 + 8, py - 5, disp + cur, 1.3, (1, 1, 1))

    def _draw_msg(self):
        if self.ui_msg and time.time() - self.ui_msg_t < 5:
            tw = TextRenderer.text_width(self.ui_msg, 1.3)
            TextRenderer.draw_text((self.W - tw) / 2, self.H * 0.12, self.ui_msg, 1.3, (1, 0.4, 0.4))

    def _draw_hint(self, text):
        tw = TextRenderer.text_width(text, 0.9)
        TextRenderer.draw_text((self.W - tw) / 2, 8, text, 0.9, (0.45, 0.45, 0.55))

    def _cleanup(self):
        if self.world and self.player:
            self.world.save(self.player.pos(), self.player.rot())
        if self.renderer:
            self.renderer.cleanup()


if __name__ == '__main__':
    try:
        game = Game()
        game.run()
    except Exception as e:
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")
