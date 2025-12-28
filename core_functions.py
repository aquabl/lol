import pymysql
import hashlib
import joblib
import pandas as pd

# ---------------------- 仅需修改这里 ----------------------
DB_PASSWORD = "308350"
MODEL_PATH = "XGBoost_LOL预测模型.joblib"  # 模型文件名（和文件夹里的一致）
# ---------------------------------------------------------

# 数据库连接工具
def get_db_connection():
    conn = pymysql.connect(
        host="localhost",
        port=3306,
        user="root",
        password=DB_PASSWORD,
        database="moba_db",
        charset="utf8mb4"
    )
    return conn

# 用户注册
def user_register(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        encrypted_pwd = hashlib.sha256(password.encode()).hexdigest()
        insert_sql = "INSERT INTO user_info (username, password) VALUES (%s, %s);"
        cursor.execute(insert_sql, (username, encrypted_pwd))
        conn.commit()
        return True, "注册成功！"
    except pymysql.IntegrityError:
        return False, "用户名已存在！"
    except Exception as e:
        return False, f"注册失败：{str(e)}"
    finally:
        cursor.close()
        conn.close()

# 用户登录
def user_login(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        encrypted_pwd = hashlib.sha256(password.encode()).hexdigest()
        query_sql = "SELECT user_id FROM user_info WHERE username=%s AND password=%s;"
        cursor.execute(query_sql, (username, encrypted_pwd))
        result = cursor.fetchone()
        if result:
            return True, result[0]
        else:
            return False, "用户名或密码错误！"
    except Exception as e:
        return False, f"登录失败：{str(e)}"
    finally:
        cursor.close()
        conn.close()

# 分类特征转独热编码
def cat_to_onehot(val):
    if val == "蓝方":
        return 1, 0, 0
    elif val == "红方":
        return 0, 1, 0
    elif val == "无":
        return 0, 0, 1

# 核心预测功能
def predict_match(user_id, firstBlood, firstTower, firstInhibitor, firstBaron, firstDragon, firstRiftHerald,
                  tower_diff, inhibitor_diff, baron_diff, dragon_diff, herald_diff):
    fb_blue, fb_red, fb_none = cat_to_onehot(firstBlood)
    ft_blue, ft_red, ft_none = cat_to_onehot(firstTower)
    fi_blue, fi_red, fi_none = cat_to_onehot(firstInhibitor)
    fb_b_blue, fb_b_red, fb_b_none = cat_to_onehot(firstBaron)
    fd_blue, fd_red, fd_none = cat_to_onehot(firstDragon)
    frh_blue, frh_red, frh_none = cat_to_onehot(firstRiftHerald)

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        insert_game_sql = """
        INSERT INTO game_match (
            user_id, firstBlood_blue, firstBlood_red, firstBlood_none,
            firstTower_blue, firstTower_red, firstTower_none,
            firstInhibitor_blue, firstInhibitor_red, firstInhibitor_none,
            firstBaron_blue, firstBaron_red, firstBaron_none,
            firstDragon_blue, firstDragon_red, firstDragon_none,
            firstRiftHerald_blue, firstRiftHerald_red, firstRiftHerald_none,
            tower_diff, inhibitor_diff, baron_diff, dragon_diff, herald_diff
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        cursor.execute(insert_game_sql, (
            user_id, fb_blue, fb_red, fb_none,
            ft_blue, ft_red, ft_none,
            fi_blue, fi_red, fi_none,
            fb_b_blue, fb_b_red, fb_b_none,
            fd_blue, fd_red, fd_none,
            frh_blue, frh_red, frh_none,
            tower_diff, inhibitor_diff, baron_diff, dragon_diff, herald_diff
        ))
        match_id = cursor.lastrowid
        conn.commit()

        model = joblib.load(MODEL_PATH)
        features = [
            fb_blue, fb_red, fb_none,
            ft_blue, ft_red, ft_none,
            fi_blue, fi_red, fi_none,
            fb_b_blue, fb_b_red, fb_b_none,
            fd_blue, fd_red, fd_none,
            frh_blue, frh_red, frh_none,
            tower_diff, inhibitor_diff, baron_diff, dragon_diff, herald_diff
        ]

        blue_win_prob = model.predict_proba([features])[0][1]
        predicted_result = "胜" if blue_win_prob >= 0.5 else "负"

        insert_result_sql = """
        INSERT INTO predict_result (user_id, match_id, blue_win_prob, predicted_result)
        VALUES (%s, %s, %s, %s);
        """
        cursor.execute(insert_result_sql, (user_id, match_id, round(blue_win_prob, 3), predicted_result))
        conn.commit()

        return True, {
            "match_id": match_id,
            "blue_win_prob": round(blue_win_prob, 3),
            "predicted_result": predicted_result
        }
    except Exception as e:
        conn.rollback()
        return False, f"预测失败：{str(e)}"
    finally:
        cursor.close()
        conn.close()

# 查询历史记录
def get_prediction_history(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    try:
        query_sql = """
        SELECT 
            p.result_id, p.match_id, p.blue_win_prob, p.predicted_result, p.predict_time
        FROM predict_result p
        JOIN game_match g ON p.match_id = g.match_id
        WHERE p.user_id = %s
        ORDER BY p.predict_time DESC;
        """
        cursor.execute(query_sql, (user_id,))
        history = cursor.fetchall()
        return True, history
    except Exception as e:
        return False, f"查询失败：{str(e)}"
    finally:
        cursor.close()
        conn.close()
