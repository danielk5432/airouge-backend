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
    # C#의 'def' 필드와 매칭시키기 위해 alias를 사용합니다.
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

# --- 최종 캐릭터 데이터 모델 (수정됨) ---
class CharacterData(BaseModel):
    id: Optional[str] = None
    character_name: str
    description: str
    # 'image_urls' (객체) 대신 'image_url' (문자열)을 받도록 수정했습니다.
    image_url: Optional[str] = None
    stats: Stats
    character_type: str
    skills: List[Skill]

# --- API 요청 모델 ---
class RunCreateRequest(BaseModel):
    player_characters: List[CharacterData]

class CharacterCreateRequest(BaseModel):
    user_prompt: str

class GameCompleteRequest(BaseModel):
    winning_characters: List[CharacterData]