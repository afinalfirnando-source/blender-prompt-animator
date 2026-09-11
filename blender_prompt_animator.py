#!/usr/bin/env python3
"""
Blender Prompt Animator
=======================
Sistem tool untuk membuat animasi video di Blender melalui text prompt.

Penggunaan:
    python blender_prompt_animator.py "prompt..."
    python blender_prompt_animator.py --prompt "prompt..."
    python blender_prompt_animator.py --file prompt.txt

Output: file .blend dan script bpy yang dapat dijalankan di Blender.
"""

import argparse
import json
import math
import os
import re
import sys
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple


# ============================================================
# DATA STRUCTURES
# ============================================================

@dataclass
class AnimationObject:
    name: str
    obj_type: str  # cube, sphere, cylinder, cone, torus, monkey, text, empty
    location: Tuple[float, float, float] = (0, 0, 0)
    rotation: Tuple[float, float, float] = (0, 0, 0)
    scale: Tuple[float, float, float] = (1, 1, 1)
    color: Tuple[float, float, float, float] = (1, 1, 1, 1)  # RGBA
    material_type: str = "principled"  # principled, glass, metallic, emission, glossy, neon
    animation_type: str = "none"  # rotate, bounce, float, move, scale, orbit
    animation_params: Dict = field(default_factory=dict)


@dataclass
class LightSpec:
    light_type: str  # sun, point, spot, area
    location: Tuple[float, float, float] = (5, -5, 10)
    energy: float = 5.0
    rotation: Tuple[float, float, float] = (0, 0, 0)


@dataclass
class CameraSpec:
    location: Tuple[float, float, float] = (7, -7, 5)
    rotation: Tuple[float, float, float] = (1.15, 0, 0.785)  # ~45 degree
    lens: float = 35.0
    animation_type: str = "orbit"  # orbit, dolly, pan, zoom, follow, none
    animation_params: Dict = field(default_factory=dict)


@dataclass
class SceneSpec:
    prompt: str
    duration_seconds: float = 5.0
    fps: int = 24
    objects: List[AnimationObject] = field(default_factory=list)
    lights: List[LightSpec] = field(default_factory=list)
    camera: CameraSpec = field(default_factory=CameraSpec)
    background_color: Tuple[float, float, float, float] = (0.02, 0.02, 0.03, 1)
    world_lighting: float = 1.0
    render_engine: str = "CYCLES"
    samples: int = 128
    output_path: str = ""
    resolution: Tuple[int, int] = (1920, 1080)
    bloom: bool = False
    bloom_intensity: float = 2.5
    depth_of_field: bool = False
    dof_distance: float = 10.0
    particle_effect: str = "none"  # snow, sparks, stars, none
    tone: str = "neutral"  # romantic, dramatic, eerie, dreamy, epic, neutral
    template: str = "none"  # product_showcase, space_epic, nature_doc, abstract, cinematic
    easing: str = "ease"  # linear, ease, bounce, elastic, overshoot


# ============================================================
# PROMPT PARSER
# ============================================================

class PromptParser:
    """Parse natural language text prompt menjadi SceneSpec."""

    # Color mapping
    COLOR_MAP = {
        'red': (1.0, 0.1, 0.1, 1),
        'crimson': (0.87, 0.25, 0.29, 1),
        'dark red': (0.55, 0.0, 0.0, 1),
        'blue': (0.1, 0.3, 1.0, 1),
        'navy': (0.05, 0.1, 0.35, 1),
        'sky blue': (0.5, 0.8, 1.0, 1),
        'cyan': (0.0, 0.8, 0.9, 1),
        'green': (0.1, 0.8, 0.3, 1),
        'lime': (0.6, 0.9, 0.2, 1),
        'forest green': (0.1, 0.5, 0.2, 1),
        'yellow': (1.0, 0.9, 0.2, 1),
        'gold': (1.0, 0.85, 0.3, 1),
        'orange': (1.0, 0.6, 0.2, 1),
        'amber': (1.0, 0.7, 0.1, 1),
        'purple': (0.6, 0.3, 0.9, 1),
        'violet': (0.8, 0.6, 1.0, 1),
        'pink': (1.0, 0.5, 0.8, 1),
        'magenta': (0.9, 0.2, 0.7, 1),
        'white': (0.95, 0.95, 0.95, 1),
        'silver': (0.9, 0.92, 0.95, 1),
        'gray': (0.5, 0.5, 0.5, 1),
        'grey': (0.5, 0.5, 0.5, 1),
        'black': (0.05, 0.05, 0.05, 1),
        'brown': (0.5, 0.3, 0.15, 1),
        'metallic': (0.7, 0.7, 0.75, 1),
        'neon': (0.2, 1.0, 0.6, 1),
        'transparent': (0.8, 0.9, 1.0, 0.3),
        'merah': (1.0, 0.1, 0.1, 1),
        'red': (1.0, 0.1, 0.1, 1),
        'biru': (0.1, 0.3, 1.0, 1),
        'blue': (0.1, 0.3, 1.0, 1),
        'kuning': (1.0, 0.9, 0.2, 1),
        'yellow': (1.0, 0.9, 0.2, 1),
        'hijau': (0.1, 0.8, 0.3, 1),
        'green': (0.1, 0.8, 0.3, 1),
        'orange': (1.0, 0.6, 0.2, 1),
        'jingga': (1.0, 0.6, 0.2, 1),
        'ungu': (0.6, 0.3, 0.9, 1),
        'purple': (0.6, 0.3, 0.9, 1),
        'pink': (1.0, 0.5, 0.8, 1),
        'merah muda': (1.0, 0.5, 0.8, 1),
        'putih': (0.95, 0.95, 0.95, 1),
        'white': (0.95, 0.95, 0.95, 1),
        'hitam': (0.05, 0.05, 0.05, 1),
        'black': (0.05, 0.05, 0.05, 1),
        'coklat': (0.5, 0.3, 0.15, 1),
        'brown': (0.5, 0.3, 0.15, 1),
        'abu-abu': (0.5, 0.5, 0.5, 1),
        'gray': (0.5, 0.5, 0.5, 1),
        'emas': (1.0, 0.85, 0.3, 1),
        'silver': (0.9, 0.92, 0.95, 1),
        'perak': (0.9, 0.92, 0.95, 1),
    }

    MATERIAL_MAP = {
        'glass': 'glass',
        'kaca': 'glass',
        'glassy': 'glass',
        'transparent': 'glass',
        'tembus': 'glass',
        'metallic': 'metallic',
        'metal': 'metallic',
        'logam': 'metallic',
        'steel': 'metallic',
        'chrome': 'metallic',
        'golden': 'metallic',
        'emas': 'metallic',
        'emission': 'emission',
        'emissive': 'emission',
        'glow': 'emission',
        'bercahaya': 'emission',
        'light': 'emission',
        'cahaya': 'emission',
        'neon': 'neon',
        'glossy': 'glossy',
        'mirror': 'glossy',
        'cermin': 'glossy',
        'shiny': 'glossy',
        'polished': 'metallic',
    }

    OBJ_TYPE_MAP = {
        'cube': ('cube', 'Cube'),
        'kubus': ('cube', 'Cube'),
        'box': ('cube', 'Cube'),
        'sphere': ('sphere', 'Sphere'),
        'bola': ('sphere', 'Sphere'),
        'bola api': ('sphere', 'Sphere'),
        'cylinder': ('cylinder', 'Cylinder'),
        'silinder': ('cylinder', 'Cylinder'),
        'cone': ('cone', 'Cone'),
        'kerucut': ('cone', 'Cone'),
        'torus': ('torus', 'Torus'),
        'donat': ('torus', 'Torus'),
        'monkey': ('monkey', 'Monkey'),
        'suzanne': ('monkey', 'Monkey'),
        'kera': ('monkey', 'Monkey'),
        'text': ('text', 'Text'),
        'teks': ('text', 'Text'),
        'plane': ('plane', 'Plane'),
        'plane': ('plane', 'Plane'),
    }

    ANIM_TYPE_MAP = {
        'rotate': 'rotate',
        'rotating': 'rotate',
        'mengitari': 'rotate',
        'berputar': 'rotate',
        'spin': 'rotate',
        'bounce': 'bounce',
        'loncat': 'bounce',
        'melompat': 'bounce',
        'float': 'float',
        'mengapung': 'float',
        'move': 'move',
        'bergerak': 'move',
        'glide': 'move',
        'scale': 'scale',
        'mengubah ukuran': 'scale',
        'besar kecil': 'scale',
        'orbit': 'orbit',
        'melingkari': 'orbit',
        'patrol': 'patrol',
    }

    POSITION_KEYWORDS = {
        'left': (-3, 0, 0),
        'right': (3, 0, 0),
        'kiri': (-3, 0, 0),
        'kanan': (3, 0, 0),
        'front': (0, -3, 0),
        'behind': (0, 3, 0),
        'belakang': (0, 3, 0),
        'di depan': (0, -3, 0),
        'atas': (0, 0, 3),
        'top': (0, 0, 3),
        'bottom': (0, 0, -1),
        'bawah': (0, 0, -1),
    }

    LIGHTING_MAP = {
        'bright': 10.0,
        'dim': 2.0,
        'dark': 1.0,
        'soft': 3.0,
        'harsh': 8.0,
        'dramatic': 6.0,
        'romantic': 2.0,
        'mood': 2.5,
    }

    BACKGROUND_MAP = {
        'black': (0.0, 0.0, 0.0, 1),
        'hitam': (0.0, 0.0, 0.0, 1),
        'white': (1.0, 1.0, 1.0, 1),
        'putih': (1.0, 1.0, 1.0, 1),
        'blue': (0.02, 0.05, 0.15, 1),
        'biru': (0.02, 0.05, 0.15, 1),
        'navy': (0.01, 0.02, 0.1, 1),
        'dark': (0.01, 0.01, 0.02, 1),
        'space': (0.01, 0.01, 0.05, 1),
        'sunset': (0.3, 0.15, 0.05, 1),
        'sunset orange': (0.4, 0.2, 0.05, 1),
        'gradient': (0.1, 0.1, 0.15, 1),
        'pink': (0.3, 0.1, 0.25, 1),
        'merah muda': (0.3, 0.1, 0.25, 1),
        'purple': (0.15, 0.1, 0.3, 1),
        'ungu': (0.15, 0.1, 0.3, 1),
    }

    # Emotional tone mapping: tone keywords -> (lighting, bg, camera, bloom, dof)
    TONE_MAP = {
        'romantic': {
            'lights': [('AREA', (2, -3, 6), 300), ('POINT', (0, -5, 3), 200)],
            'bg': (0.3, 0.15, 0.2, 1),
            'camera': 'dolly',
            'bloom': True,
            'bloom_intensity': 4.0,
            'dof': True,
            'dof_distance': 5.0,
        },
        'dramatic': {
            'lights': [('SUN', (5, -5, 10), 8.0), ('AREA', (-3, -4, 5), 400)],
            'bg': (0.05, 0.03, 0.05, 1),
            'bloom': False,
            'dof': True,
            'dof_distance': 8.0,
        },
        'eerie': {
            'lights': [('POINT', (4, -4, 3), 300), ('SPOT', (-3, 4, 5), 500)],
            'bg': (0.01, 0.02, 0.05, 1),
            'camera': 'dolly',
            'bloom': True,
            'bloom_intensity': 1.5,
            'dof': True,
            'dof_distance': 6.0,
        },
        'dreamy': {
            'lights': [('SUN', (2, -5, 8), 3.0), ('AREA', (0, -5, 6), 150)],
            'bg': (0.5, 0.5, 0.6, 1),
            'camera': 'zoom',
            'bloom': True,
            'bloom_intensity': 6.0,
            'dof': True,
            'dof_distance': 7.0,
        },
        'epic': {
            'lights': [('SUN', (10, -10, 20), 12.0), ('AREA', (-8, -8, 15), 600)],
            'bg': (0.1, 0.15, 0.25, 1),
            'camera': 'orbit',
            'bloom': True,
            'bloom_intensity': 3.0,
            'dof': False,
        },
    }

    # Cinematic mood keywords
    MOOD_KEYWORDS = {
        'romantic': ['romantic', 'romantis', 'love', 'heart', 'warm'],
        'dramatic': ['dramatic', 'dramatik', 'intense', 'serious', 'serius'],
        'eerie': ['eerie', 'spooky', 'menjerikan', 'ghost', 'setengah'],
        'dreamy': ['dreamy', 'mimpi', 'pastel', 'soft focus', 'lembut'],
        'epic': ['epic', 'grand', ['greate', 'majestic'], 'epik', 'heroik'],
    }

    # Scene templates
    TEMPLATE_MAP = {
        'product_showcase': {
            'camera': 'dolly',
            'camera_location': (5, -5, 2),
            'lights': [('AREA', (3, -3, 5), 1000), ('AREA', (-3, -3, 5), 500), ('AREA', (0, 0, 8), 300)],
            'bg': (0.05, 0.05, 0.05, 1),
            'dof': True,
            'dof_distance': 4.0,
            'easing': 'ease',
        },
        'space_epic': {
            'camera': 'orbit',
            'camera_location': (15, -15, 10),
            'lights': [('SUN', (10, -10, 20), 5.0)],
            'bg': (0.0, 0.0, 0.05, 1),
            'particle_effect': 'stars',
            'bloom': True,
            'bloom_intensity': 2.0,
            'easing': 'ease',
        },
        'nature_doc': {
            'camera': 'follow',
            'camera_location': (8, -8, 4),
            'lights': [('SUN', (5, -5, 10), 4.0), ('AREA', (-5, 5, 8), 200)],
            'bg': (0.05, 0.1, 0.05, 1),
            'easing': 'ease',
        },
        'abstract': {
            'camera': 'pan',
            'camera_location': (12, -12, 8),
            'lights': [('POINT', (5, -5, 5), 200), ('POINT', (-5, 5, 5), 200)],
            'bg': (0.1, 0.1, 0.15, 1),
            'bloom': True,
            'bloom_intensity': 3.5,
            'easing': 'elastic',
        },
        'cinematic': {
            'camera': 'dolly',
            'camera_location': (6, -6, 3),
            'lights': [('SUN', (3, -5, 10), 6.0), ('AREA', (-4, -4, 6), 300)],
            'bg': (0.02, 0.02, 0.05, 1),
            'dof': True,
            'dof_distance': 6.0,
            'easing': 'ease',
        },
    }

    @staticmethod
    def parse(prompt: str) -> SceneSpec:
        prompt_lower = prompt.lower().strip()
        spec = SceneSpec(prompt=prompt)

        # Parse duration
        spec.duration_seconds, spec.fps = PromptParser._parse_duration(prompt_lower)

        # Parse resolution
        spec.resolution = PromptParser._parse_resolution(prompt_lower)

        # Parse render engine
        spec.render_engine, spec.samples = PromptParser._parse_render_engine(prompt_lower)

        # Parse background
        spec.background_color = PromptParser._parse_background(prompt_lower)

        # Parse objects
        spec.objects = PromptParser._parse_objects(prompt_lower)

        # Parse lighting
        spec.lights = PromptParser._parse_lights(prompt_lower)

        # Parse camera
        spec.camera = PromptParser._parse_camera(prompt_lower)

        # Parse effects
        spec.bloom = 'bloom' in prompt_lower or 'glow' in prompt_lower or 'bercahaya' in prompt_lower
        spec.depth_of_field = 'depth of field' in prompt_lower or 'bokeh' in prompt_lower or 'dof' in prompt_lower
        if 'snow' in prompt_lower or 'salju' in prompt_lower:
            spec.particle_effect = "snow"
        elif 'spark' in prompt_lower or 'semolar' in prompt_lower:
            spec.particle_effect = "sparks"
        elif 'star' in prompt_lower or 'bintang' in prompt_lower:
            spec.particle_effect = "stars"

        # Parse emotional tone
        spec.tone = PromptParser._parse_tone(prompt_lower)

        # Parse easing
        spec.easing = PromptParser._parse_easing(prompt_lower)

        # Parse scene template
        spec.template = PromptParser._parse_template(prompt_lower)

        # Save explicit camera animation from user prompt
        explicit_camera = spec.camera.animation_type

        # Apply template overrides
        if spec.template != "none":
            PromptParser._apply_template(spec)

        # Apply tone overrides
        PromptParser._apply_tone(spec, prompt_lower)

        # Restore explicit camera if user specified one
        if explicit_camera != "orbit":
            spec.camera.animation_type = explicit_camera

        # Auto-generate objects if none found
        if not spec.objects:
            spec.objects = PromptParser._generate_default_objects(prompt_lower)

        return spec

    @staticmethod
    def _parse_duration(text: str) -> Tuple[float, int]:
        duration = 5.0
        fps = 24

        # Match patterns like "5 seconds", "10s", "3 detik"
        dur_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:seconds?|s|detik)', text)
        if dur_match:
            duration = float(dur_match.group(1))

        # Match FPS
        fps_match = re.search(r'(\d+)\s*fps', text)
        if fps_match:
            fps = int(fps_match.group(1))

        return duration, fps

    @staticmethod
    def _parse_resolution(text: str) -> Tuple[int, int]:
        # Match patterns like "1920x1080", "1080p", "4k", "hd"
        res_match = re.search(r'(\d+)\s*[xX×]\s*(\d+)', text)
        if res_match:
            return (int(res_match.group(1)), int(res_match.group(2)))

        if '4k' in text or 'uhd' in text:
            return (3840, 2160)
        if '1080p' in text or 'full hd' in text:
            return (1920, 1080)
        if '720p' in text or 'hd' in text:
            return (1280, 720)

        return (1920, 1080)

    @staticmethod
    def _parse_render_engine(text: str) -> Tuple[str, int]:
        if 'cycles' in text:
            return ('CYCLES', 128)
        if 'eevee' in text or 'eevee' in text:
            return ('BLENDER_EEVEE', 64)
        if 'wireframe' in text or 'garis' in text:
            return ('BLENDER_EEVEE', 1)
        # Default
        return ('CYCLES', 128)

    @staticmethod
    def _parse_background(text: str) -> Tuple[float, float, float, float]:
        for bg_name, bg_color in PromptParser.BACKGROUND_MAP.items():
            if bg_name in text:
                return bg_color
        return (0.02, 0.02, 0.03, 1)

    @staticmethod
    def _parse_color(text: str) -> Tuple[float, float, float, float]:
        for color_name, color_val in PromptParser.COLOR_MAP.items():
            if color_name in text:
                return color_val
        return (1, 1, 1, 1)

    @staticmethod
    def _parse_objects(text: str) -> List[AnimationObject]:
        objects = []
        found_types = set()

        # Normalize: split into tokens for flexible color+object detection
        # Approach: find each object type keyword, then look around it for a color
        all_obj_types = [
            'cube', 'kubus', 'box', 'sphere', 'bola', 'cylinder', 'silinder',
            'cone', 'kerucut', 'torus', 'donat', 'monkey', 'suzanne', 'kera',
            'text', 'teks', 'plane', 'planet', 'grid', 'floor', 'lantai', 'ring', 'cincin'
        ]

        for obj_keyword in all_obj_types:
            # Find all positions of this object keyword in text (word-boundary, allow optional plural 's')
            pattern = r'\b' + re.escape(obj_keyword) + r's?\b'
            for match in re.finditer(pattern, text):
                start = match.start()
                end = match.end()

                # Look at text before the object for a color (up to 30 chars back)
                text_before = text[max(0, start - 30):start]
                text_after = text[end:end + 30]
                context = text_before + obj_keyword + text_after

                color = PromptParser._parse_color(context)

                # Determine normalized object type
                if obj_keyword in ('cube', 'kubus', 'box'):
                    ot = 'cube'
                elif obj_keyword in ('sphere', 'bola', 'planet'):
                    ot = 'sphere'
                elif obj_keyword in ('cylinder', 'silinder'):
                    ot = 'cylinder'
                elif obj_keyword in ('cone', 'kerucut'):
                    ot = 'cone'
                elif obj_keyword in ('torus', 'donat', 'ring', 'cincin'):
                    ot = 'torus'
                elif obj_keyword in ('monkey', 'suzanne', 'kera'):
                    ot = 'monkey'
                elif obj_keyword in ('text', 'teks'):
                    ot = 'text'
                elif obj_keyword in ('plane', 'grid', 'lantai', 'floor'):
                    ot = 'plane'
                else:
                    ot = 'plane'

                if ot in found_types:
                    continue
                found_types.add(ot)

                anim_type = PromptParser._detect_animation(context)
                mat_type = PromptParser._parse_material(context)
                obj = AnimationObject(
                    name=f"Object_{len(objects) + 1}",
                    obj_type=ot,
                    color=color,
                    material_type=mat_type,
                    animation_type=anim_type
                )
                pos = PromptParser._parse_position(text, len(objects))
                obj.location = pos
                objects.append(obj)

        # If no colored objects found, check for plain object mentions
        if not found_types:
            for pattern_name, (ot, display_name) in PromptParser.OBJ_TYPE_MAP.items():
                if pattern_name in text and ot not in found_types:
                    anim_type = PromptParser._detect_animation(text)
                    obj = AnimationObject(
                        name=f"Object_{len(objects) + 1}",
                        obj_type=ot,
                        color=(0.8, 0.3, 0.3, 1),
                        animation_type=anim_type
                        )
                    pos = PromptParser._parse_position(text, len(objects))
                    obj.location = pos
                    objects.append(obj)
                    found_types.add(ot)

        return objects

    @staticmethod
    def _detect_animation(text: str) -> str:
        for keyword, anim_type in PromptParser.ANIM_TYPE_MAP.items():
            if keyword in text:
                return anim_type
        return "rotate"  # default animation

    @staticmethod
    def _parse_material(text: str) -> str:
        for keyword, mat_type in PromptParser.MATERIAL_MAP.items():
            if keyword in text:
                return mat_type
        return "principled"

    @staticmethod
    def _parse_tone(text: str) -> str:
        for tone, keywords in PromptParser.MOOD_KEYWORDS.items():
            for kw in keywords:
                if isinstance(kw, list):
                    if all(k in text for k in kw):
                        return tone
                elif kw in text:
                    return tone
        return "neutral"

    @staticmethod
    def _parse_easing(text: str) -> str:
        easing_map = {
            'linear': ['linear', 'linier'],
            'ease': ['ease', 'smooth', 'halus'],
            'bounce': ['bounce', 'memantul', 'rebound'],
            'elastic': ['elastic', 'elastik', 'snap'],
            'overshoot': ['overshoot', 'lepas', 'kendur'],
        }
        # Check longer keywords first to avoid substring conflicts (e.g., "elastic" contains "ease")
        for easing_type, keywords in easing_map.items():
            for kw in keywords:
                if re.search(r'\b' + re.escape(kw) + r'\b', text):
                    return easing_type
        return "ease"

    @staticmethod
    def _parse_template(text: str) -> str:
        for template_name in PromptParser.TEMPLATE_MAP.keys():
            if template_name in text or template_name.replace('_', ' ') in text:
                return template_name
        # Fuzzy match common keywords
        if 'product' in text or 'showcase' in text:
            return "product_showcase"
        if 'space' in text or 'galaxy' in text or 'astronomy' in text:
            return "space_epic"
        if 'nature' in text or 'documentary' in text or 'outdoor' in text:
            return "nature_doc"
        if 'abstract' in text or 'minimal' in text:
            return "abstract"
        if 'cinematic' in text or 'film' in text or 'movie' in text:
            return "cinematic"
        return "none"

    @staticmethod
    def _apply_template(spec: SceneSpec):
        tmpl = PromptParser.TEMPLATE_MAP.get(spec.template)
        if not tmpl:
            return

        if 'camera' in tmpl:
            if spec.camera.animation_type == "orbit":
                spec.camera.animation_type = tmpl['camera']
        if 'camera_location' in tmpl:
            spec.camera.location = tmpl['camera_location']
        # Only override lights if template specifies them
        if 'lights' in tmpl:
            spec.lights = [LightSpec(light_type=lt, location=loc, energy=en) for lt, loc, en in tmpl['lights']]
        if 'bg' in tmpl:
            spec.background_color = tmpl['bg']
        if 'particle_effect' in tmpl and spec.particle_effect == "none":
            spec.particle_effect = tmpl['particle_effect']
        if 'bloom' in tmpl and not spec.bloom:
            spec.bloom = tmpl['bloom']
        if 'bloom_intensity' in tmpl:
            spec.bloom_intensity = tmpl['bloom_intensity']
        if 'dof' in tmpl and not spec.depth_of_field:
            spec.depth_of_field = tmpl['dof']
        if 'dof_distance' in tmpl:
            spec.dof_distance = tmpl['dof_distance']
        if 'easing' in tmpl:
            if spec.easing == "ease":  # only override if not explicitly set
                spec.easing = tmpl['easing']

    @staticmethod
    def _apply_tone(spec: SceneSpec, text: str):
        tone_cfg = PromptParser.TONE_MAP.get(spec.tone)
        if not tone_cfg:
            return

        if 'lights' in tone_cfg and not spec.template:
            spec.lights = [LightSpec(light_type=lt, location=loc, energy=en) for lt, loc, en in tone_cfg['lights']]
        if 'bg' in tone_cfg:
            spec.background_color = tone_cfg['bg']
        if 'camera' in tone_cfg:
            spec.camera.animation_type = tone_cfg['camera']
        if 'bloom' in tone_cfg:
            spec.bloom = tone_cfg['bloom']
        if 'bloom_intensity' in tone_cfg:
            spec.bloom_intensity = tone_cfg['bloom_intensity']
        if 'dof' in tone_cfg:
            spec.depth_of_field = tone_cfg['dof']
        if 'dof_distance' in tone_cfg:
            spec.dof_distance = tone_cfg['dof_distance']

    @staticmethod
    def _parse_position(text: str, obj_index: int) -> Tuple[float, float, float]:
        for keyword, pos in PromptParser.POSITION_KEYWORDS.items():
            if keyword in text:
                # Offset based on index
                x = pos[0] + (obj_index * 2.5 if pos[0] == 0 else 0)
                return (x, pos[1], pos[2])
        return (0, 0, 0)

    @staticmethod
    def _parse_lights(text: str) -> List[LightSpec]:
        lights = []
        
        # Detect lighting keywords
        if 'sunset' in text or 'sunset' in text:
            lights.append(LightSpec(light_type='SUN', location=(5, -5, 10), energy=3.5))
        
        if 'studio' in text or 'dramatic' in text:
            lights.append(LightSpec(light_type='SUN', location=(5, -5, 10), energy=5.0, rotation=(0.5, 0.3, 0)))
            lights.append(LightSpec(light_type='AREA', location=(-3, -3, 7), energy=200, rotation=(0, 0, 0)))
        
        for keyword, energy in PromptParser.LIGHTING_MAP.items():
            if keyword in text and not lights:
                lights.append(LightSpec(light_type='SUN', location=(5, -5, 10), energy=energy))
        
        if not lights:
            # Default lighting
            lights.append(LightSpec(light_type='SUN', location=(5, -5, 10), energy=4.0))
            lights.append(LightSpec(light_type='AREA', location=(-4, -4, 6), energy=300))
        
        return lights

    @staticmethod
    def _parse_camera(text: str) -> CameraSpec:
        camera = CameraSpec()

        if 'close up' in text or 'dekat' in text:
            camera.location = (3, -3, 2)
        elif 'wide' in text or 'luas' in text:
            camera.location = (10, -10, 7)
        elif 'overhead' in text or 'dari atas' in text:
            camera.location = (0, -10, 10)
            camera.rotation = (0, 0, 0)
        elif 'low angle' in text or 'dari bawah' in text:
            camera.location = (0, -10, -2)
            camera.rotation = (0, 0, 0)

        # Detect camera animation
        if 'dolly' in text:
            camera.animation_type = "dolly"
        elif 'pan' in text or 'mengelilingi' in text:
            camera.animation_type = "pan"
        elif 'zoom' in text or 'memzoom' in text:
            camera.animation_type = "zoom"
        elif 'follow' in text or 'mengikuti' in text:
            camera.animation_type = "follow"

        return camera

    @staticmethod
    def _generate_default_objects(text: str) -> List[AnimationObject]:
        """Generate default objects when none found in prompt."""
        objects = []
        
        if 'cube' in text or 'kubus' in text:
            objects.append(AnimationObject(
                name="DefaultCube",
                obj_type="cube",
                color=(0.8, 0.3, 0.3, 1),
                material_type=PromptParser._parse_material(text),
                animation_type=PromptParser._detect_animation(text)
            ))
        elif 'sphere' in text or 'bola' in text:
            objects.append(AnimationObject(
                name="DefaultSphere",
                obj_type="sphere",
                color=(0.3, 0.6, 1.0, 1),
                material_type=PromptParser._parse_material(text),
                animation_type=PromptParser._detect_animation(text)
            ))
        elif 'monkey' in text or 'suzanne' in text:
            objects.append(AnimationObject(
                name="Suzanne",
                obj_type="monkey",
                color=(0.8, 0.6, 0.2, 1),
                material_type=PromptParser._parse_material(text),
                animation_type=PromptParser._detect_animation(text)
            ))
        else:
            # Default: a cube and sphere
            objects.append(AnimationObject(
                name="Cube",
                obj_type="cube",
                location=(-2, 0, 0),
                color=(0.8, 0.3, 0.3, 1),
                animation_type="rotate"
            ))
            objects.append(AnimationObject(
                name="Sphere",
                obj_type="sphere",
                location=(2, 0, 0),
                color=(0.3, 0.6, 1.0, 1),
                animation_type="bounce"
            ))
        
        return objects


# ============================================================
# BLENDER SCRIPT GENERATOR
# ============================================================

class BlenderScriptGenerator:
    """Generate Blender Python script from SceneSpec."""

    @staticmethod
    def generate(spec: SceneSpec, output_blend: str = "", output_render: str = "") -> str:
        lines = []
        lines.append('"""Auto-generated Blender script by Blender Prompt Animator."""')
        lines.append('import bpy')
        lines.append('import math')
        lines.append('import os')
        lines.append('')
        lines.append('')

        # Clean scene
        lines.append('# --- Clean scene ---')
        lines.append('bpy.ops.wm.read_factory_settings(use_empty=True)')
        lines.append('')

        # World background
        lines.append('# --- World settings ---')
        bg = spec.background_color
        lines.append(f'world = bpy.data.worlds.new("World")')
        lines.append(f'bpy.context.scene.world = world')
        lines.append(f'world.use_nodes = True')
        lines.append(f'bg_nodes = world.node_tree.nodes')
        lines.append(f'bg_nodes.clear()')
        lines.append(f'tex_coord = bg_nodes.new(type="ShaderNodeTexCoord")')
        lines.append(f'tex_coord.location = (-300, 0)')
        lines.append(f'bg = bg_nodes.new(type="ShaderNodeBackground")')
        lines.append(f'bg.location = (0, 0)')
        lines.append(f'bg.outputs["Color"].default_value = ({bg[0]:.4f}, {bg[1]:.4f}, {bg[2]:.4f}, {bg[3]:.4f})')
        lines.append(f'bg.outputs["Roughness"].default_value = 0.8')
        lines.append(f'output = bg_nodes.new(type="ShaderNodeOutputWorld")')
        lines.append(f'output.location = (200, 0)')
        lines.append(f'links = world.node_tree.links')
        lines.append(f'links.new(tex_coord.outputs["Window"], bg.inputs["Color"])')
        lines.append(f'links.new(bg.outputs["Background"], output.inputs["Surface"])')
        lines.append(f'world.light_settings.use_ambient_occlusion = True')
        lines.append(f'world.light_settings.ao_factor = {spec.world_lighting}')
        lines.append('')

        # Render settings
        lines.append('# --- Render settings ---')
        lines.append(f'render = bpy.context.scene.render')
        lines.append(f'render.engine = "{spec.render_engine}"')
        lines.append(f'render.resolution_x = {spec.resolution[0]}')
        lines.append(f'render.resolution_y = {spec.resolution[1]}')
        lines.append(f'render.resolution_percentage = 100')
        lines.append(f'render.fps = {spec.fps}')
        lines.append(f'render.frame_start = 1')
        num_frames = int(spec.duration_seconds * spec.fps)
        lines.append(f'render.frame_end = {num_frames}')
        if spec.render_engine == "CYCLES":
            lines.append(f'bpy.context.scene.cycles.samples = {spec.samples}')
            lines.append(f'bpy.context.scene.cycles.preview_samples = 8')
        else:
            lines.append(f'bpy.context.scene.eevee.taa_render_samples = 64')
        lines.append('')

        # Lights
        lines.append('# --- Lights ---')
        for i, light in enumerate(spec.lights):
            light_name = f"Light_{i+1}_{light.light_type}"
            lines.append(f'light_data = bpy.data.lights.new(name="{light_name}", type="{light.light_type}")')
            lines.append(f'light_data.energy = {light.energy}')
            if light.light_type == 'AREA':
                lines.append(f'light_data.shape = "RECTANGLE"')
                lines.append(f'light_data.size = 5.0')
                lines.append(f'light_data.size_y = 3.0')
            lines.append(f'light_obj = bpy.data.objects.new("{light_name}", light_data)')
            lines.append(f'bpy.context.collection.objects.link(light_obj)')
            lx, ly, lz = light.location
            lines.append(f'light_obj.location = ({lx}, {ly}, {lz})')
            if light.rotation != (0, 0, 0):
                rx, ry, rz = light.rotation
                lines.append(f'light_obj.rotation_mode = "XYZ"')
                lines.append(f'light_obj.rotation_euler = ({rx}, {ry}, {rz})')
        lines.append('')

        # Camera
        lines.append('# --- Camera ---')
        lines.append(f'cam_data = bpy.data.cameras.new(name="CameraAnim")')
        lines.append(f'cam_obj = bpy.data.objects.new("CameraAnim", cam_data)')
        lines.append(f'bpy.context.collection.objects.link(cam_obj)')
        lines.append(f'bpy.context.scene.camera = cam_obj')
        cx, cy, cz = spec.camera.location
        lines.append(f'cam_obj.location = ({cx}, {cy}, {cz})')
        crx, cry, crz = spec.camera.rotation
        lines.append(f'cam_obj.rotation_mode = "XYZ"')
        lines.append(f'cam_obj.rotation_euler = ({crx}, {cry}, {crz})')
        lines.append(f'cam_data.lens = {spec.camera.lens}')
        lines.append('')

        # Objects
        lines.append('# --- Objects ---')
        for i, obj in enumerate(spec.objects):
            obj_name = obj.name
            obj_var = f"obj_{i}"
            
            if obj.obj_type == 'cube':
                lines.append(f'bpy.ops.mesh.primitive_cube_add(size=2)')
                lines.append(f'{obj_var} = bpy.context.active_object')
                lines.append(f'{obj_var}.name = "{obj_name}"')
            elif obj.obj_type == 'sphere':
                lines.append(f'bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=64, ring_freq=32)')
                lines.append(f'{obj_var} = bpy.context.active_object')
                lines.append(f'{obj_var}.name = "{obj_name}"')
            elif obj.obj_type == 'cylinder':
                lines.append(f'bpy.ops.mesh.primitive_cylinder_add(radius=1, depth=2)')
                lines.append(f'{obj_var} = bpy.context.active_object')
                lines.append(f'{obj_var}.name = "{obj_name}"')
            elif obj.obj_type == 'cone':
                lines.append(f'bpy.ops.mesh.primitive_cone_add(radius1=1, radius2=0, depth=2)')
                lines.append(f'{obj_var} = bpy.context.active_object')
                lines.append(f'{obj_var}.name = "{obj_name}"')
            elif obj.obj_type == 'torus':
                lines.append(f'bpy.ops.mesh.primitive_torus_add(major_radius=1.5, minor_radius=0.5)')
                lines.append(f'{obj_var} = bpy.context.active_object')
                lines.append(f'{obj_var}.name = "{obj_name}"')
            elif obj.obj_type == 'monkey':
                lines.append(f'bpy.ops.mesh.primitive_monkey_add()')
                lines.append(f'{obj_var} = bpy.context.active_object')
                lines.append(f'{obj_var}.name = "{obj_name}"')
            elif obj.obj_type == 'text':
                lines.append(f'bpy.ops.object.text_add()')
                lines.append(f'{obj_var} = bpy.context.active_object')
                lines.append(f'{obj_var}.name = "{obj_name}"')
                lines.append(f'{obj_var}.data.body = "Hello"')
                lines.append(f'{obj_var}.data.size = 3')
                lines.append(f'{obj_var}.data.extrude = 0.1')
            elif obj.obj_type == 'plane':
                lines.append(f'bpy.ops.mesh.primitive_plane_add(size=5)')
                lines.append(f'{obj_var} = bpy.context.active_object')
                lines.append(f'{obj_var}.name = "{obj_name}"')
            else:
                lines.append(f'bpy.ops.mesh.primitive_cube_add(size=2)')
                lines.append(f'{obj_var} = bpy.context.active_object')
                lines.append(f'{obj_var}.name = "{obj_name}"')

            # Material/color - based on material type
            r, g, b, a = obj.color
            lines.append(f'')
            lines.append(f'mat_{i} = bpy.data.materials.new(name="{obj_name}_Mat")')
            lines.append(f'mat_{i}.use_nodes = True')
            lines.append(f'bsdf_nodes = mat_{i}.node_tree.nodes')
            lines.append(f'principled = bsdf_nodes.get("Principled BSDF")')

            if obj.material_type == "glass":
                lines.append(f'# Glass material')
                lines.append(f'principled.inputs["Base Color"].default_value = ({r:.4f}, {g:.4f}, {b:.4f}, 1)')
                lines.append(f'principled.inputs["Roughness"].default_value = 0.05')
                lines.append(f'principled.inputs["IOR"].default_value = 1.45')
                lines.append(f'principled.inputs["Transmission"].default_value = 1.0')
                lines.append(f'principled.inputs["Alpha"].default_value = 0.3')
                lines.append(f'mat_{i}.blend_method = "HASHED"')
                lines.append(f'mat_{i}.shadow_method = "HASHED"')
            elif obj.material_type == "metallic":
                lines.append(f'# Metallic material')
                lines.append(f'principled.inputs["Base Color"].default_value = ({r:.4f}, {g:.4f}, {b:.4f}, 1)')
                lines.append(f'principled.inputs["Metallic"].default_value = 1.0')
                lines.append(f'principled.inputs["Roughness"].default_value = 0.15')
            elif obj.material_type == "emission":
                lines.append(f'# Emission material')
                lines.append(f'principled.inputs["Base Color"].default_value = ({r:.4f}, {g:.4f}, {b:.4f}, 1)')
                lines.append(f'principled.inputs["Emission"].default_value = 1.0')
                lines.append(f'principled.inputs["Roughness"].default_value = 0.0')
                lines.append(f'principled.inputs["Emission Strength"].default_value = 5.0')
                lines.append(f'mat_{i}.use_fake_user = True')
                # Add emission node
                lines.append(f'_emission = bsdf_nodes.new(type="ShaderNodeEmission")')
                lines.append(f'_emission.inputs["Color"].default_value = ({r:.4f}, {g:.4f}, {b:.4f}, 1)')
                lines.append(f'_emission.inputs["Strength"].default_value = 2.0')
                lines.append(f'bsdf_nodes.link(_emission.outputs["Emission"], principled.inputs["Emission"])')
            elif obj.material_type == "neon":
                lines.append(f'# Neon glow material')
                lines.append(f'principled.inputs["Base Color"].default_value = ({r:.4f}, {g:.4f}, {b:.4f}, 1)')
                lines.append(f'principled.inputs["Emission"].default_value = 1.0')
                lines.append(f'principled.inputs["Roughness"].default_value = 0.0')
                lines.append(f'principled.inputs["Specular"].default_value = 0.9')
                lines.append(f'_emission = bsdf_nodes.new(type="ShaderNodeEmission")')
                lines.append(f'_emission.inputs["Color"].default_value = ({r:.4f}, {g:.4f}, {b:.4f}, 1)')
                lines.append(f'_emission.inputs["Strength"].default_value = 10.0')
                lines.append(f'bsdf_nodes.link(_emission.outputs["Emission"], principled.inputs["Emission"])')
            elif obj.material_type == "glossy":
                lines.append(f'# Glossy material')
                lines.append(f'principled.inputs["Base Color"].default_value = ({r:.4f}, {g:.4f}, {b:.4f}, 1)')
                lines.append(f'principled.inputs["Metallic"].default_value = 0.0')
                lines.append(f'principled.inputs["Specular"].default_value = 0.9')
                lines.append(f'principled.inputs["Roughness"].default_value = 0.05')
            else:
                lines.append(f'# Principled material')
                lines.append(f'principled.inputs["Base Color"].default_value = ({r:.4f}, {g:.4f}, {b:.4f}, {a:.4f})')
                if r > 0.8 and g > 0.8 and b > 0.8:
                    lines.append(f'principled.inputs["Roughness"].default_value = 0.1')
                    lines.append(f'principled.inputs["Metallic"].default_value = 0.9')
                elif a < 0.5:
                    lines.append(f'mat_{i}.blend_method = "BLEND"')
                    lines.append(f'principled.inputs["Alpha"].default_value = {a:.4f}')
                    lines.append(f'principled.inputs["Roughness"].default_value = 0.2')
                else:
                    lines.append(f'principled.inputs["Roughness"].default_value = 0.4')
            lines.append(f'{obj_var}.data.materials.append(mat_{i})')

            # Position
            ox, oy, oz = obj.location
            lines.append(f'{obj_var}.location = ({ox}, {oy}, {oz})')
            sx, sy, sz = obj.scale
            lines.append(f'{obj_var}.scale = ({sx}, {sy}, {sz})')
            lines.append(f'')

            # Animation
            if obj.animation_type != "none":
                lines.extend(BlenderScriptGenerator._generate_animation(obj_var, obj.animation_type, i, spec))

        # Camera animation
        cam_anim = spec.camera.animation_type
        lines.append('')
        lines.append('# --- Camera animation ---')
        if cam_anim == "dolly":
            lines.append(f'# Dolly: move camera toward subject')
            lines.append(f'cam_obj.keyframe_insert(data_path="location", frame=1)')
            lines.append(f'cam_obj.location = ({cx / 2}, {cy / 2}, {cz / 2})')
            lines.append(f'cam_obj.keyframe_insert(data_path="location", frame={num_frames})')
        elif cam_anim == "zoom":
            lines.append(f'# Zoom: change focal length')
            lines.append(f'cam_data.lens = {spec.camera.lens}')
            lines.append(f'cam_data.keyframe_insert(data_path="lens", frame=1)')
            lines.append(f'cam_data.lens = 85.0')
            lines.append(f'cam_data.keyframe_insert(data_path="lens", frame={num_frames})')
        elif cam_anim == "pan":
            lines.append(f'# Pan: orbit camera around center')
            for cf in range(4):
                frame_num = int(num_frames * (cf + 1) / 4)
                offset = cf * math.pi / 2
                new_x = cx * math.cos(offset) - cy * math.sin(offset)
                new_y = cx * math.sin(offset) + cy * math.cos(offset)
                lines.append(f'cam_obj.location = ({new_x:.2f}, {new_y:.2f}, {cz})')
                lines.append(f'cam_obj.keyframe_insert(data_path="location", frame={frame_num})')
        elif cam_anim == "follow":
            lines.append(f'# Follow: camera tracks objects')
            lines.append(f'follow_obj = bpy.data.objects.new("FollowPath", None)')
            lines.append(f'follow_obj.location = (0, 0, 0)')
            lines.append(f'bpy.context.collection.objects.link(follow_obj)')
            lines.append(f'cam_obj.constraints.new(type="TRACK_TO")')
            lines.append(f'cam_obj.constraints["Track To"].target = follow_obj')
            lines.append(f'cam_obj.constraints["Track To"].track_axis = "TRACK_NEGATIVE_Z"')
            lines.append(f'cam_obj.constraints["Track To"].up_axis = "UP_Y"')
            lines.append(f'cam_obj.keyframe_insert(data_path="location", frame=1)')
            lines.append(f'cam_obj.location = ({cx + 2}, {cy - 2}, {cz})')
            lines.append(f'cam_obj.keyframe_insert(data_path="location", frame={num_frames})')
        else:
            lines.append(f'# Subtle orbit movement')
            lines.append(f'cam_obj.keyframe_insert(data_path="location", frame=1)')
            lines.append(f'cam_obj.location = ({cx}, {cy}, {cz + 0.5})')
            lines.append(f'cam_obj.keyframe_insert(data_path="location", frame={num_frames})')
            lines.append(f'cam_obj.rotation_euler = ({crx}, {cry}, {crz + 0.1})')
            lines.append(f'cam_obj.keyframe_insert(data_path="rotation_euler", frame={num_frames})')

        # Post-processing
        if spec.bloom:
            lines.append('')
            lines.append('# --- Bloom / Glow ---')
            lines.append(f'render.engine = "BLENDER_EEVEE"')
            lines.append(f'bpy.context.scene.render.engine = "BLENDER_EEVEE"')
            lines.append(f'bpy.context.view_layer.eevee.use_bloom = True')
            lines.append(f'bpy.context.view_layer.eevee.bloom_intensity = {spec.bloom_intensity}')
            lines.append(f'bpy.context.view_layer.eevee.bloom_radius = 6.5')
            lines.append(f'bpy.context.view_layer.eevee.bloom_color = (1, 1, 1)')
        if spec.depth_of_field:
            lines.append('')
            lines.append('# --- Depth of Field ---')
            lines.append(f'cam_data.dof.use_dof = True')
            lines.append(f'cam_data.dof.focus_distance = {spec.dof_distance}')
            lines.append(f'cam_data.dof.aperture_fstop = 2.8')

        # Particle effects
        if spec.particle_effect != "none":
            lines.extend(BlenderScriptGenerator._generate_particles(spec.particle_effect, num_frames))

        # Output path
        if output_render:
            lines.append('')
            lines.append('# --- Output ---')
            escaped_path = output_render.replace('\\', '/')
            lines.append(f'render.filepath = "{escaped_path}"')
            lines.append(f'render.image_settings.file_format = "FFMPEG"')
            lines.append(f'render.ffmpeg.format = "MPEG4"')
            lines.append(f'render.ffmpeg.codec = "H264"')
            lines.append(f'render.ffmpeg.output_format = "MOVIE"')
            lines.append(f'print("Rendering animation...")')
            lines.append(f'bpy.ops.render.render(write_to_file=True, animation=True)')
            lines.append(f'print("Video rendered!")')

        lines.append('')
        lines.append('print("Scene setup complete!")')
        lines.append('')

        return '\n'.join(lines)

    @staticmethod
    def _generate_particles(effect_type: str, total_frames: int) -> List[str]:
        lines = []
        lines.append('')
        lines.append('# --- Particle Effects ---')

        if effect_type == "snow":
            lines.append(f'bpy.ops.object.light_add(type="POINT", location=(0, 0, 10))')
            lines.append(f'_psys_obj = bpy.context.active_object')
            lines.append(f'_psys_obj.hide_viewport = True')
            lines.append(f'_psys_obj.hide_render = True')
            lines.append(f'_psys_psys = _psys_obj.modifiers.new(name="SnowParticles", type="PARTICLE_SYSTEM")')
            lines.append(f'_psys_settings = _psys_psys.particle_system.settings')
            lines.append(f'_psys_settings.count = 500')
            lines.append(f'_psys_settings.frame_start = 1')
            lines.append(f'_psys_settings.frame_end = {total_frames}')
            lines.append(f'_psys_settings.lifetime = 100')
            lines.append(f'_psys_settings.emit_from = "FACE"')
            lines.append(f'_psys_settings.use_global_dupli = True')
            lines.append(f'_psys_settings.render_type = "HALO"')
            lines.append(f'_psys_settings.particle_size = 0.1')
            lines.append(f'_psys_settings.use_rotations = True')
            lines.append(f'_psys_settings.use_dynamic_rotation = True')
            lines.append(f'_psys_settings.normal_factor = 0.0')
            lines.append(f'_psys_settings.use_global_dupli = True')
            # Add volume for particle emission
            lines.append(f'bpy.ops.mesh.primitive_cube_add(size=20)')
            lines.append(f'_snow_domain = bpy.context.active_object')
            lines.append(f'_snow_domain.name = "SnowDomain"')
            lines.append(f'_snow_domain.hide_viewport = True')
            lines.append(f'_snow_domain.hide_render = True')
            lines.append(f'_snow_domain.location = (0, 0, 0)')
            lines.append(f'_psys_settings.instance_object = None')
            lines.append(f'_psys_particle_mat = bpy.data.materials.new(name="SnowMat")')
            lines.append(f'_psys_particle_mat.use_nodes = True')
            lines.append(f'_psys_pnodes = _psys_particle_mat.node_tree.nodes')
            lines.append(f'_psys_pr = _psys_pnodes.get("Principled BSDF")')
            lines.append(f'_psys_pr.inputs["Base Color"].default_value = (1, 1, 1, 1)')
            lines.append(f'_psys_pr.inputs["Roughness"].default_value = 0.1')
            lines.append(f'_psys_pr.inputs["Transmission"].default_value = 0.9')
            lines.append(f'_psys_pr.inputs["IOR"].default_value = 1.33')
            lines.append(f'_psys_particle_mat.blend_method = "HASHED"')

        elif effect_type == "sparks":
            lines.append(f'bpy.ops.object.light_add(type="POINT", location=(0, 0, 5))')
            lines.append(f'_spark_obj = bpy.context.active_object')
            lines.append(f'_spark_obj.hide_viewport = True')
            lines.append(f'_spark_obj.hide_render = True')
            lines.append(f'_spark_psys = _spark_obj.modifiers.new(name="SparkParticles", type="PARTICLE_SYSTEM")')
            lines.append(f'_spark_settings = _spark_psys.particle_system.settings')
            lines.append(f'_spark_settings.count = 300')
            lines.append(f'_spark_settings.frame_start = 1')
            lines.append(f'_spark_settings.frame_end = {total_frames}')
            lines.append(f'_spark_settings.lifetime = 50')
            lines.append(f'_spark_settings.emit_from = "VOLUME"')
            lines.append(f'_spark_settings.render_type = "HALO"')
            lines.append(f'_spark_settings.particle_size = 0.05')
            lines.append(f'_spark_settings.use_rotations = True')
            lines.append(f'bpy.ops.mesh.primitive_uv_sphere_add(radius=3)')
            lines.append(f'_spark_domain = bpy.context.active_object')
            lines.append(f'_spark_domain.name = "SparkDomain"')
            lines.append(f'_spark_domain.hide_viewport = True')
            lines.append(f'_spark_domain.hide_render = True')

        elif effect_type == "stars":
            lines.append(f'bpy.ops.mesh.primitive_cube_add(size=50)')
            lines.append(f'_star_domain = bpy.context.active_object')
            lines.append(f'_star_domain.name = "StarDomain"')
            lines.append(f'_star_domain.hide_viewport = True')
            lines.append(f'_star_domain.hide_render = True')
            lines.append(f'_star_psys = _star_domain.modifiers.new(name="StarParticles", type="PARTICLE_SYSTEM")')
            lines.append(f'_star_settings = _star_psys.particle_system.settings')
            lines.append(f'_star_settings.count = 1000')
            lines.append(f'_star_settings.frame_start = 1')
            lines.append(f'_star_settings.frame_end = {total_frames}')
            lines.append(f'_star_settings.lifetime = 0')
            lines.append(f'_star_settings.emit_from = "VOLUME"')
            lines.append(f'_star_settings.render_type = "HALO"')
            lines.append(f'_star_settings.particle_size = 0.2')
            lines.append(f'_star_settings.use_global_dupli = True')
            lines.append(f'_star_mat = bpy.data.materials.new(name="StarMat")')
            lines.append(f'_star_mat.use_nodes = True')
            lines.append(f'_star_pnodes = _star_mat.node_tree.nodes')
            lines.append(f'_star_pr = _star_pnodes.get("Principled BSDF")')
            lines.append(f'_star_pr.inputs["Base Color"].default_value = (1, 1, 0.8, 1)')
            lines.append(f'_star_pr.inputs["Emission"].default_value = 1.0')
            lines.append(f'_star_emission = _star_pnodes.new(type="ShaderNodeEmission")')
            lines.append(f'_star_emission.inputs["Color"].default_value = (1, 1, 0.9, 1)')
            lines.append(f'_star_emission.inputs["Strength"].default_value = 3.0')

        return lines

    @staticmethod
    def _generate_animation(obj_var: str, anim_type: str, obj_idx: int, spec: SceneSpec) -> List[str]:
        fps = spec.fps
        duration = spec.duration_seconds
        total_frames = int(duration * fps)
        quarter = total_frames // 4
        half = total_frames // 2
        
        lines = []
        lines.append(f'# --- Animation for {obj_var} ---')
        
        # Get current location
        lines.append(f'import math')
        lines.append(f'_loc = {obj_var}.location')
        lines.append(f'_start_frame = 1')
        lines.append(f'{obj_var}.keyframe_insert(data_path="location", frame=_start_frame)')
        
        if anim_type == "rotate":
            lines.append(f'# Full rotation')
            lines.append(f'{obj_var}.rotation_mode = "XYZ"')
            lines.append(f'{obj_var}.rotation_euler = (0, 0, 0)')
            lines.append(f'{obj_var}.keyframe_insert(data_path="rotation_euler", frame=1)')
            lines.append(f'{obj_var}.rotation_euler = (0, 0, {2 * math.pi:.6f})')
            lines.append(f'{obj_var}.keyframe_insert(data_path="rotation_euler", frame={total_frames})')
            lines.append(f'for _f in range(1, {total_frames + 1}):')
            lines.append(f'    _t = _f / {total_frames}')
            lines.append(f'    {obj_var}.location = (_loc[0], _loc[1], _loc[2] + 0.2 * math.sin(_t * 4 * {math.pi:.6f}))')
            lines.append(f'    {obj_var}.keyframe_insert(data_path="location", frame=_f)')
            
        elif anim_type == "bounce":
            lines.append(f'# Bouncing animation')
            lines.append(f'for _f in range(1, {total_frames + 1}):')
            lines.append(f'    _t = _f / {total_frames}')
            lines.append(f'    _bounce = abs(math.sin(_t * 4 * {math.pi:.6f}))')
            lines.append(f'    {obj_var}.location = (_loc[0], _loc[1], _loc[2] + _bounce * 2.5)')
            lines.append(f'    {obj_var}.keyframe_insert(data_path="location", frame=_f)')
            # Add squash and stretch
            lines.append(f'    _squash = 1.0 - _bounce * 0.2')
            lines.append(f'    {obj_var}.scale = (1 + _bounce * 0.3, _squash, 1 + _bounce * 0.3)')
            lines.append(f'    {obj_var}.keyframe_insert(data_path="scale", frame=_f)')
            
        elif anim_type == "float":
            lines.append(f'# Floating animation')
            lines.append(f'for _f in range(1, {total_frames + 1}):')
            lines.append(f'    _t = _f / {total_frames}')
            lines.append(f'    {obj_var}.location = (_loc[0], _loc[1], _loc[2] + math.sin(_t * 2 * {math.pi:.6f}) * 1.5)')
            lines.append(f'    {obj_var}.keyframe_insert(data_path="location", frame=_f)')
            lines.append(f'    _rot = _t * 2 * {math.pi:.6f}')
            lines.append(f'    {obj_var}.rotation_mode = "XYZ"')
            lines.append(f'    {obj_var}.rotation_euler = (0, 0, _rot)')
            lines.append(f'    {obj_var}.keyframe_insert(data_path="rotation_euler", frame=_f)')

        elif anim_type == "move":
            lines.append(f'# Moving animation')
            lines.append(f'for _f in range(1, {total_frames + 1}):')
            lines.append(f'    _t = _f / {total_frames}')
            lines.append(f'    _new_x = _loc[0] + math.sin(_t * 2 * {math.pi:.6f}) * 4')
            lines.append(f'    {obj_var}.location = (_new_x, _loc[1], _loc[2])')
            lines.append(f'    {obj_var}.keyframe_insert(data_path="location", frame=_f)')

        elif anim_type == "scale":
            lines.append(f'# Scaling animation')
            lines.append(f'for _f in range(1, {total_frames + 1}):')
            lines.append(f'    _t = _f / {total_frames}')
            lines.append(f'    _scale = 1.0 + math.sin(_t * 2 * {math.pi:.6f}) * 0.5')
            lines.append(f'    {obj_var}.scale = (_scale, _scale, _scale)')
            lines.append(f'    {obj_var}.keyframe_insert(data_path="scale", frame=_f)')

        elif anim_type == "orbit":
            lines.append(f'# Orbit animation')
            lines.append(f'for _f in range(1, {total_frames + 1}):')
            lines.append(f'    _t = _f / {total_frames}')
            lines.append(f'    _angle = _t * 2 * {math.pi:.6f}')
            lines.append(f'    _radius = 3.0')
            lines.append(f'    {obj_var}.location = (_loc[0] + math.cos(_angle) * _radius, _loc[1] + math.sin(_angle) * _radius, _loc[2])')
            lines.append(f'    {obj_var}.keyframe_insert(data_path="location", frame=_f)')
            lines.append(f'    {obj_var}.rotation_mode = "XYZ"')
            lines.append(f'    {obj_var}.rotation_euler = (0, 0, _angle + {math.pi:.6f})')
            lines.append(f'    {obj_var}.keyframe_insert(data_path="rotation_euler", frame=_f)')

        elif anim_type == "patrol":
            lines.append(f'# Patrol animation')
            lines.append(f'_patrol_dist = 4.0')
            lines.append(f'for _f in range(1, {total_frames + 1}):')
            lines.append(f'    _t = _f / {total_frames}')
            lines.append(f'    _new_x = _loc[0] + math.sin(_t * 2 * {math.pi:.6f}) * _patrol_dist')
            lines.append(f'    {obj_var}.location = (_new_x, _loc[1], _loc[2])')
            lines.append(f'    {obj_var}.keyframe_insert(data_path="location", frame=_f)')

        # Apply easing based on spec.easing
        easing_map = {
            'linear': 'LINEAR',
            'ease': 'BEZ',
            'bounce': 'BOUNCE',
            'elastic': 'ELASTIC',
            'overshoot': 'BACK',
        }
        easing_interp = easing_map.get(spec.easing, 'BEZ')

        if spec.easing == "linear":
            lines.append(f'# Linear interpolation')
            lines.append(f'if {obj_var}.animation_data and {obj_var}.animation_data.action:')
            lines.append(f'    for _fc in {obj_var}.animation_data.action.fcurves:')
            lines.append(f'        _fc.modifiers.new(type="CYCLES")')
            lines.append(f'        for _kp in _fc.keyframe_points:')
            lines.append(f'            _kp.interpolation = "LINEAR"')
        else:
            lines.append(f'# Easing: {spec.easing}')
            lines.append(f'if {obj_var}.animation_data and {obj_var}.animation_data.action:')
            lines.append(f'    for _fc in {obj_var}.animation_data.action.fcurves:')
            if spec.easing == "bounce":
                lines.append(f'        _mod = _fc.modifiers.new(type="BOUNCE")')
                lines.append(f'        _mod.keyframe_id = "location"')
            elif spec.easing == "elastic":
                lines.append(f'        for _kp in _fc.keyframe_points:')
                lines.append(f'            _kp.interpolation = "BEZ"')
                lines.append(f'            _kp.easing = "AUTO_CLAMPED"')
            elif spec.easing == "overshoot":
                lines.append(f'        for _kp in _fc.keyframe_points:')
                lines.append(f'            _kp.interpolation = "BEZ"')
                lines.append(f'            _kp.easing = "EASE_INOUT"')
                lines.append(f'        _mod = _fc.modifiers.new(type="LIMITS")')
            else:
                lines.append(f'        for _kp in _fc.keyframe_points:')
                lines.append(f'            _kp.interpolation = "{easing_interp}"')
                lines.append(f'            _kp.easing = "EASE_INOUT"')

        lines.append(f'')
        return lines


# ============================================================
# MAIN / CLI
# ============================================================

class BlenderPromptAnimator:
    def __init__(self, workspace_dir: str = None):
        self.workspace_dir = workspace_dir or os.getcwd()
        self.output_dir = os.path.join(self.workspace_dir, "blender_output")
        os.makedirs(self.output_dir, exist_ok=True)

    def process_prompt(self, prompt: str, render: bool = False) -> dict:
        """Process a text prompt and generate Blender animation."""
        
        # Parse prompt
        spec = PromptParser.parse(prompt)
        
        # Set output paths
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
        script_path = os.path.join(self.output_dir, f"anim_{timestamp}.py")
        blend_path = os.path.join(self.output_dir, f"anim_{timestamp}.blend")
        render_path = os.path.join(self.output_dir, f"render_{timestamp}")
        
        # Generate script
        script_content = BlenderScriptGenerator.generate(
            spec, 
            output_blend=blend_path,
            output_render=render_path if render else ""
        )
        
        # Write script file
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # Generate metadata
        metadata = {
            "prompt": prompt,
            "timestamp": timestamp,
            "script_file": script_path,
            "blend_file": blend_path,
            "render_file": render_path + ".mp4" if render else None,
            "scene_spec": {
                "duration_seconds": spec.duration_seconds,
                "fps": spec.fps,
                "resolution": spec.resolution,
                "render_engine": spec.render_engine,
                "samples": spec.samples,
                "objects": [
                    {
                        "name": o.name,
                        "type": o.obj_type,
                        "color": list(o.color),
                        "animation_type": o.animation_type,
                        "material_type": o.material_type,
                        "location": list(o.location)
                    } for o in spec.objects
                ],
                "lights": [
                    {"type": l.light_type, "energy": l.energy, "location": list(l.location)}
                    for l in spec.lights
                ],
                "camera": {
                    "location": list(spec.camera.location),
                    "rotation": list(spec.camera.rotation),
                    "lens": spec.camera.lens,
                    "animation_type": spec.camera.animation_type
                },
                "background": list(spec.background_color),
                "tone": spec.tone,
                "template": spec.template,
                "easing": spec.easing,
                "bloom": spec.bloom,
                "bloom_intensity": spec.bloom_intensity,
                "depth_of_field": spec.depth_of_field,
                "dof_distance": spec.dof_distance,
                "particle_effect": spec.particle_effect,
                "total_frames": int(spec.duration_seconds * spec.fps)
            }
        }
        
        return metadata

    def run_in_blender(self, script_path: str, blender_path: str = None) -> str:
        """Run the generated script in Blender."""
        if blender_path is None:
            # Default Blender path
            blender_path = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
        
        cmd = f'"{blender_path}" --background --python "{script_path}"'
        return cmd


def main():
    parser = argparse.ArgumentParser(
        description="Blender Prompt Animator - Create animations from text prompts"
    )
    parser.add_argument("prompt", nargs="?", help="Text prompt describing the animation")
    parser.add_argument("--prompt", "-p", dest="prompt_opt", help="Text prompt (alternative)")
    parser.add_argument("--file", "-f", help="File containing the prompt")
    parser.add_argument("--render", action="store_true", help="Render the animation to video")
    parser.add_argument("--blender", "-b", help="Path to blender executable")
    parser.add_argument("--workspace", "-w", help="Workspace directory")
    parser.add_argument("--ci", action="store_true", help="CI/fast mode: Eevee, low samples, 1080p")
    parser.add_argument("--all", action="store_true", help="Generate and render all prompts from a file")
    
    args = parser.parse_args()
    
    # Create animator early
    animator = BlenderPromptAnimator(args.workspace)
    
    # Apply CI overrides to the spec after parsing
    def process_prompt_ci(prompt_text, render_flag):
        metadata = animator.process_prompt(prompt_text, render=render_flag)
        spec = PromptParser.parse(prompt_text)
        spec.render_engine = "BLENDER_EEVEE"
        spec.samples = 16
        script_content = BlenderScriptGenerator.generate(
            spec,
            output_blend=metadata['blend_file'],
            output_render=metadata['render_file'].replace('.mp4', '') if render_flag else ""
        )
        with open(metadata['script_file'], 'w', encoding='utf-8') as f:
            f.write(script_content)
        return metadata
    
    # Get prompt
    prompt = args.prompt_opt or args.prompt or args.file
    if not prompt:
        print("Error: No prompt provided")
        print("Usage: python blender_prompt_animator.py \"red cube rotating, 5 seconds\"")
        print("       python blender_prompt_animator.py --prompt \"...\"")
        print("       python blender_prompt_animator.py --file prompt.txt")
        print("       python blender_prompt_animator.py --all --file pond5_seamless.txt --ci --render")
        sys.exit(1)
    
    if args.all and args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            file_content = f.read().strip()
        prompts = [p.strip() for p in file_content.split('\n') if p.strip()]
        print(f"=== Processing {len(prompts)} prompts ===")
        for i, p in enumerate(prompts, 1):
            print(f"\n--- [{i}/{len(prompts)}] ---")
            if args.ci:
                p = p.replace('4k', '1080p').replace('4K', '1080p')
                p += ' eevee'
                metadata = process_prompt_ci(p, args.render)
            else:
                metadata = animator.process_prompt(p, render=args.render)
            metadata_path = os.path.join(animator.output_dir, f"meta_{metadata['timestamp']}.json")
            with open(metadata_path, 'w', encoding='utf-8') as mf:
                json.dump(metadata, mf, indent=2, ensure_ascii=False)
            print(f"Script: {metadata['script_file']}")
            if args.render:
                cmd = animator.run_in_blender(metadata['script_file'], args.blender)
                print(f"Command: {cmd}")
        print(f"\n=== All {len(prompts)} prompts processed ===")
        sys.exit(0)
    
    if args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            prompt = f.read().strip()
    
    # Process
    if args.ci:
        metadata = process_prompt_ci(prompt, args.render)
    else:
        metadata = animator.process_prompt(prompt, render=args.render)
    
    # Save metadata
    metadata_path = os.path.join(animator.output_dir, f"meta_{metadata['timestamp']}.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    # Output results
    print("=== Blender Prompt Animator ===")
    print(f"Prompt: {metadata['prompt']}")
    print(f"Script: {metadata['script_file']}")
    if metadata['render_file']:
        print(f"Render: {metadata['render_file']}")
    print(f"Frames: {metadata['scene_spec']['total_frames']}")
    print(f"Objects: {len(metadata['scene_spec']['objects'])}")
    for obj in metadata['scene_spec']['objects']:
        print(f"  - {obj['name']} ({obj['type']}) color={obj['color']} anim={obj['animation_type']}")
    print(f"Lights: {len(metadata['scene_spec']['lights'])}")
    print(f"Background: {metadata['scene_spec']['background']}")
    print(f"Metadata: {metadata_path}")
    
    # If render flag, provide Blender command
    if args.render:
        cmd = animator.run_in_blender(metadata['script_file'], args.blender)
        print(f"\nBlender command:\n{cmd}")
    
    return metadata


if __name__ == "__main__":
    main()
