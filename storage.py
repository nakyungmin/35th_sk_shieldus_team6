# MongoDB 저장·조회. 연결이 안 되면 JSON 파일을 쓴다.
# 직접 실행하면(python storage.py) JSON 내용을 MongoDB에 다시 넣는다.

import json

import config

COLLECTIONS = ["hospital", "facility", "park", "registration", "stats"]

# 연결은 한 번만 시도하고 결과를 기억한다 (꺼져 있을 때 매번 기다리지 않게)
db_checked = False
db_connection = None


def load_json(name):
    with open(f"{config.PROCESSED_DIR}/{name}.json", encoding="utf-8") as f:
        return json.load(f)


def get_db():
    """연결되면 DB, 안 되면 None."""
    global db_checked, db_connection
    if db_checked:
        return db_connection

    db_checked = True
    try:
        from pymongo import MongoClient
        client = MongoClient(config.MONGO_URI, serverSelectionTimeoutMS=1500)
        client.admin.command("ping")
        db_connection = client[config.MONGO_DB]
    except Exception:
        db_connection = None
    return db_connection


def save_one(name, rows):
    """name 컬렉션을 rows로 통째로 바꾼다. 성공하면 True."""
    db = get_db()
    if db is None:
        return False

    # insert_many가 '_id'를 붙이므로 복사본을 넣는다
    copies = []
    for row in rows:
        copies.append(dict(row))

    db[name].delete_many({})
    if len(copies) > 0:
        db[name].insert_many(copies)

    if name in ["hospital", "facility", "park"]:
        db[name].create_index([("sido", 1), ("city", 1)])
    return True


def save_all():
    for name in COLLECTIONS:
        rows = load_json(name)
        if not save_one(name, rows):
            print("MongoDB에 연결하지 못했습니다. MongoDB가 켜져 있는지, pymongo가 설치됐는지 확인하세요.")
            return
        print(f"  {name}: {len(rows)}건 저장")
    print("MongoDB 저장 끝")


def load(name, sido=None, city=None):
    """MongoDB에서, 없으면 JSON에서 읽는다. city를 주면 그 지역만."""
    db = get_db()
    if db is not None and db[name].count_documents({}) > 0:
        if city:
            query = {"sido": sido, "city": city}
        else:
            query = {}
        return list(db[name].find(query, {"_id": 0}))

    rows = load_json(name)
    if not city:
        return rows

    result = []
    for row in rows:
        if row["sido"] == sido and row["city"] == city:
            result.append(row)
    return result


if __name__ == "__main__":
    save_all()
