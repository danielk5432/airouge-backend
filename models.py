from pydantic import BaseModel, Field
from typing import List, Optional

# --- 스킬 연출 관련 모델 ---
class ShakeEffect(BaseModel):
    particle_color: str

class ProjectileEffect(BaseModel):
    shape: str
    count: int
    color: str

class LaserEffect(BaseModel):
    origin: str
    thickness: int
    color: str

# --- 스킬 모델 ---
class Skill(BaseModel):
    skill_name: str
    description: str
    base_power: int
    damage_type: str
    skill_type: str
    visual_effect_type: str # Unity Enum과 매칭: "Shake", "Projectile", "Laser"
    shake_effect: Optional[ShakeEffect] = None
    projectile_effect: Optional[ProjectileEffect] = None
    laser_effect: Optional[LaserEffect] = None

# --- 능력치 모델 ---
class Stats(BaseModel):
    hp: int
    atk: int
    # 'def'는 Python 예약어와 겹칠 수 있어 alias를 사용하거나 다른 이름을 쓰는 것이 안전합니다.
    # 여기서는 그대로 def를 사용하되, 문제가 생기면 def_stat 등으로 변경할 수 있습니다.
    def_stat: int = Field(alias="def")
    sp_atk: int
    sp_def: int
    speed: int

# --- 이미지 URL 모델 ---
class ImageUrls(BaseModel):
    standing: Optional[str] = None
    victory: Optional[str] = None
    defeat: Optional[str] = None
    attacking: Optional[str] = None
    hit: Optional[str] = None

# --- 최종 캐릭터 데이터 모델 ---
class CharacterData(BaseModel):
    id: Optional[str] = None
    character_name: str
    description: str
    image_urls: Optional[ImageUrls] = None # 5종 이미지 세트
    stats: Stats
    character_type: str
    skills: List[Skill]

# --- API 요청 모델 ---
class RunCreateRequest(BaseModel):
    player_characters: List[CharacterData]

class CharacterCreateRequest(BaseModel):
    user_prompt: str