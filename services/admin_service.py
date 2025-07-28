import json
import os

CHARACTER_FILE = "static/characters.json"

def get_all_characters_from_file():
    """characters.json 파일에서 모든 캐릭터 목록을 불러옵니다."""
    try:
        with open(CHARACTER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return [] # 파일이 없거나 비어있으면 빈 리스트 반환

def save_character_to_file(character_data: dict):
    """새로운 캐릭터 하나를 파일에 추가합니다."""
    characters = get_all_characters_from_file()
    characters.append(character_data)
    with open(CHARACTER_FILE, "w", encoding="utf-8") as f:
        json.dump(characters, f, ensure_ascii=False, indent=2)
    return character_data

def delete_character_from_file(character_id: str):
    """ID를 기준으로 캐릭터를 삭제하고, 연관된 이미지 파일도 삭제합니다."""
    characters = get_all_characters_from_file()
    
    char_to_delete = None
    # 삭제할 캐릭터를 찾습니다.
    for char in characters:
        if char.get('id') == character_id:
            char_to_delete = char
            break
    
    # 캐릭터를 찾지 못했다면, False를 반환합니다.
    if not char_to_delete:
        return False

    # --- 이미지 파일 삭제 로직 추가 ---
    image_url = char_to_delete.get('image_url')
    if image_url:
        # URL 경로 (예: /static/images/...)를 실제 파일 시스템 경로 (예: static/images/...)로 변환합니다.
        # lstrip('/')은 맨 앞의 '/'만 안전하게 제거합니다.
        image_path = image_url.lstrip('/')
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
                print(f"이미지 파일 삭제 성공: {image_path}")
            except OSError as e:
                print(f"이미지 파일 삭제 실패: {e}")
        else:
            print(f"삭제할 이미지 파일을 찾을 수 없음: {image_path}")
    # --------------------------------

    # 캐릭터 데이터 리스트에서 해당 캐릭터를 제외합니다.
    updated_characters = [char for char in characters if char.get('id') != character_id]
    
    # 업데이트된 리스트를 다시 JSON 파일에 씁니다.
    with open(CHARACTER_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_characters, f, ensure_ascii=False, indent=2)
        
    return True