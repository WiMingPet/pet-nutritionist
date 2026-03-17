import streamlit as st
import pandas as pd
import datetime
import random
import os
import sqlite3
import plotly.express as px
import plotly.graph_objects as go
from aip import AipImageClassify  # 百度AI的SDK

# ========== 页面美化设置 ==========
st.set_page_config(
    page_title="宠物AI营养师", 
    page_icon="🐱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    /* 全局字体设置 */
    .stApp {
        background-color: #f9f9f9;
    }
    
    /* 标题样式 */
    h1 {
        color: #FF6B6B;
        font-size: 3rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    /* 副标题样式 */
    h2 {
        color: #4ECDC4;
        font-size: 2rem;
        font-weight: 600;
    }
    
    h3 {
        color: #45B7D1;
        font-size: 1.5rem;
        font-weight: 500;
    }
    
    /* 卡片样式 */
    .stApp [data-testid="stVerticalBlock"] {
        background-color: transparent;
    }
    
    /* 按钮样式 */
    .stButton button {
        background-color: #4ECDC4;
        color: white;
        border-radius: 20px;
        border: none;
        padding: 0.5rem 2rem;
        font-size: 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        background-color: #45B7D1;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    /* 输入框样式 */
    .stTextInput input, .stNumberInput input {
        border-radius: 10px;
        border: 2px solid #E0E0E0;
        padding: 0.5rem;
    }
    
    .stTextInput input:focus, .stNumberInput input:focus {
        border-color: #4ECDC4;
        box-shadow: 0 0 0 2px rgba(78,205,196,0.2);
    }
    
    /* 标签页样式 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        background-color: white;
        padding: 0.5rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 20px;
        padding: 0.5rem 1.5rem;
        font-weight: 500;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #4ECDC4;
        color: white;
    }
    
    /* 进度条样式 */
    .stProgress > div > div {
        background-color: #4ECDC4;
        border-radius: 10px;
    }
    
    /* 成功消息样式 */
    .stAlert {
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# 页面顶部装饰
st.markdown("""
<div style='text-align: center; padding: 1rem;'>
    <h1>🐱 宠物AI营养师</h1>
    <p style='color: #6C757D; font-size: 1.2rem;'>为你的毛孩子定制健康饮食计划</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ========== 百度AI配置 ==========
# 从Streamlit Secrets读取密钥
APP_ID = st.secrets.get("APP_ID", '122401445')
API_KEY = st.secrets.get("API_KEY", 's0Ci5vaSBEYA1VT4Ez9jH5j6')
SECRET_KEY = st.secrets.get("SECRET_KEY", '9yqsGkNOXopZpsDNPKmauO7kaNn5p1nc')

# 初始化百度AI客户端
client_bd = AipImageClassify(APP_ID, API_KEY, SECRET_KEY)

# ========== 本地数据库操作 ==========
DB_FILE = "pet_records.db"  # 数据库文件名

def init_database():
    """初始化数据库，创建表（如果不存在）"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # 创建宠物表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_name TEXT NOT NULL,
            pet_type TEXT NOT NULL,
            pet_gender TEXT,
            birth_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建饮食记录表（增加pet_id字段）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS diet_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pet_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            food_name TEXT NOT NULL,
            amount INTEGER NOT NULL,
            calories INTEGER NOT NULL,
            protein REAL NOT NULL,
            meal_time TEXT,
            FOREIGN KEY (pet_id) REFERENCES pets (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# 初始化数据库
init_database()

# 初始化会话状态
if 'history' not in st.session_state:
    st.session_state.history = []

# ========== 宠物管理函数 ==========
def add_pet(pet_name, pet_type, pet_gender, birth_date):
    """添加新宠物到数据库"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO pets (pet_name, pet_type, pet_gender, birth_date)
            VALUES (?, ?, ?, ?)
        ''', (pet_name, pet_type, pet_gender, birth_date))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"添加宠物失败：{str(e)}")
        return False

def get_all_pets():
    """获取所有宠物列表"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('SELECT id, pet_name, pet_type FROM pets ORDER BY id')
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        st.error(f"获取宠物列表失败：{str(e)}")
        return []

def get_pet_info(pet_id):
    """获取指定宠物信息"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM pets WHERE id = ?', (pet_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                'id': row[0],
                'pet_name': row[1],
                'pet_type': row[2],
                'pet_gender': row[3],
                'birth_date': row[4]
            }
        return None
    except Exception as e:
        st.error(f"获取宠物信息失败：{str(e)}")
        return None

def save_record_to_db(record):
    """保存记录到本地SQLite数据库（新版本）"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO diet_records (pet_id, food_name, amount, calories, protein, meal_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            record['pet_id'],
            record['food_name'],
            record['amount'],
            record['calories'],
            record['protein'],
            record['meal_time']
        ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        st.error(f"保存到数据库失败：{str(e)}")
        return False

def load_records_from_db(pet_id):
    """从本地数据库加载指定宠物的今天记录"""
    try:
        # 获取今天的日期
        today = datetime.datetime.now().date()
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT strftime('%H:%M', created_at), food_name, calories, protein
            FROM diet_records
            WHERE pet_id = ? AND date(created_at) = date(?)
            ORDER BY created_at
        ''', (pet_id, today.isoformat()))
        rows = cursor.fetchall()
        conn.close()
        
        # 转换成字典列表
        records = []
        for row in rows:
            records.append({
                '时间': row[0],
                '食物': row[1],
                '热量': row[2],
                '蛋白质': row[3]
            })
        return records
    except Exception as e:
        st.error(f"从数据库加载失败：{str(e)}")
        return []

def load_history_records(pet_id, days=30):
    """加载指定宠物的历史记录（用于图表）"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT date(created_at) as record_date, 
                   SUM(calories) as total_calories,
                   SUM(protein) as total_protein,
                   COUNT(*) as meal_count
            FROM diet_records
            WHERE pet_id = ? AND created_at >= date('now', ?)
            GROUP BY date(created_at)
            ORDER BY record_date
        ''', (pet_id, f'-{days} days'))
        rows = cursor.fetchall()
        conn.close()
        
        # 转换成字典列表
        records = []
        for row in rows:
            records.append({
                '日期': row[0],
                '总热量': row[1] or 0,
                '总蛋白质': row[2] or 0,
                '餐数': row[3] or 0
            })
        return records
    except Exception as e:
        st.error(f"加载历史记录失败：{str(e)}")
        return []

# ========== 食物数据库（扩展版50+种）==========
@st.cache_data
def load_food_database():
    data = {
        '食物名称': [
            # 猫粮狗粮类
            '猫粮（干）', '猫粮（湿）', '幼猫粮', '老年猫粮', '处方猫粮（肾脏）', '处方猫粮（肠胃）',
            '狗粮（干）', '狗粮（湿）', '幼犬粮', '老年犬粮', '大型犬专用粮', '小型犬专用粮',
            '处方狗粮（关节）', '处方狗粮（减肥）',
            
            # 肉类
            '鸡胸肉', '鸡腿肉', '鸡肝', '鸡心',
            '牛肉', '牛肝', '牛心',
            '猪肉', '猪肝',
            '羊肉', '羊肝',
            '鸭肉', '火鸡肉',
            '兔肉', '鹿肉',
            
            # 鱼类海鲜
            '三文鱼', '金枪鱼', '鳕鱼', '鲭鱼', '沙丁鱼',
            '虾仁', '贻贝', '扇贝', '螃蟹肉',
            
            # 蛋奶类
            '鸡蛋', '鸭蛋', '鹌鹑蛋',
            '酸奶', '奶酪', '羊奶',
            
            # 蔬菜类
            '胡萝卜', '南瓜', '西兰花', '菠菜', '白菜', '黄瓜',
            '红薯', '土豆', '山药',
            '豌豆', '青豆', '玉米',
            
            # 水果类
            '苹果', '香蕉', '蓝莓', '草莓', '西瓜', '木瓜',
            
            # 谷物类
            '米饭', '燕麦', '小米', '糙米', '全麦面包',
            
            # 营养补充剂
            '鱼油', '益生菌', '软骨素', '钙粉', '维生素B族', '牛磺酸'
        ],
        '类型': [
            # 猫粮狗粮类
            '猫粮', '猫粮', '猫粮', '猫粮', '猫粮', '猫粮',
            '狗粮', '狗粮', '狗粮', '狗粮', '狗粮', '狗粮',
            '狗粮', '狗粮',
            
            # 肉类
            '肉类', '肉类', '内脏', '内脏',
            '肉类', '内脏', '内脏',
            '肉类', '内脏',
            '肉类', '内脏',
            '肉类', '肉类',
            '肉类', '肉类',
            
            # 鱼类海鲜
            '鱼类', '鱼类', '鱼类', '鱼类', '鱼类',
            '海鲜', '海鲜', '海鲜', '海鲜',
            
            # 蛋奶类
            '蛋类', '蛋类', '蛋类',
            '奶制品', '奶制品', '奶制品',
            
            # 蔬菜类
            '蔬菜', '蔬菜', '蔬菜', '蔬菜', '蔬菜', '蔬菜',
            '蔬菜', '蔬菜', '蔬菜',
            '蔬菜', '蔬菜', '蔬菜',
            
            # 水果类
            '水果', '水果', '水果', '水果', '水果', '水果',
            
            # 谷物类
            '谷物', '谷物', '谷物', '谷物', '谷物',
            
            # 营养补充剂
            '补充剂', '补充剂', '补充剂', '补充剂', '补充剂', '补充剂'
        ],
        '热量_kcal_100g': [
            # 猫粮狗粮类
            380, 120, 400, 350, 320, 330,
            360, 110, 380, 340, 370, 365,
            350, 300,
            
            # 肉类
            165, 170, 140, 150,
            250, 135, 140,
            240, 130,
            200, 125,
            160, 160,
            140, 130,
            
            # 鱼类海鲜
            208, 180, 90, 190, 200,
            85, 80, 90, 95,
            
            # 蛋奶类
            155, 160, 158,
            60, 400, 70,
            
            # 蔬菜类
            41, 26, 34, 23, 12, 15,
            86, 77, 65,
            80, 75, 110,
            
            # 水果类
            52, 89, 57, 32, 30, 43,
            
            # 谷物类
            130, 389, 360, 370, 265,
            
            # 营养补充剂
            900, 300, 400, 0, 0, 0
        ],
        '蛋白质_g_100g': [
            # 猫粮狗粮类
            30, 8, 32, 28, 25, 26,
            25, 7, 28, 24, 26, 25,
            24, 22,
            
            # 肉类
            31, 28, 20, 22,
            26, 22, 21,
            25, 21,
            22, 20,
            26, 26,
            22, 21,
            
            # 鱼类海鲜
            20, 22, 18, 20, 22,
            15, 16, 18, 18,
            
            # 蛋奶类
            13, 13.5, 13,
            3.5, 25, 3.2,
            
            # 蔬菜类
            0.9, 1, 2.8, 2.9, 1.2, 0.8,
            1.6, 2, 1.5,
            5, 4, 3,
            
            # 水果类
            0.3, 1.1, 0.7, 0.7, 0.6, 0.5,
            
            # 谷物类
            2.7, 16.9, 11, 7.5, 13,
            
            # 营养补充剂
            0, 0, 0, 0, 0, 0
        ],
        '脂肪_g_100g': [
            # 猫粮狗粮类
            15, 5, 16, 12, 10, 11,
            12, 4, 14, 10, 13, 12,
            10, 8,
            
            # 肉类
            3.6, 6, 4.5, 5,
            17, 4, 5,
            14, 4,
            8, 4,
            5, 5,
            3, 2,
            
            # 鱼类海鲜
            13, 10, 2, 12, 14,
            0.5, 1.5, 1, 1.5,
            
            # 蛋奶类
            11, 12, 11,
            3.5, 33, 3.8,
            
            # 蔬菜类
            0.2, 0.1, 0.4, 0.4, 0.1, 0.1,
            0.1, 0.1, 0.2,
            0.5, 0.5, 1,
            
            # 水果类
            0.2, 0.3, 0.3, 0.3, 0.2, 0.1,
            
            # 谷物类
            0.3, 6.9, 4, 2.5, 3.5,
            
            # 营养补充剂
            100, 10, 30, 0, 0, 0
        ],
        '适用宠物': [
            # 猫粮狗粮类
            '猫', '猫', '猫', '猫', '猫', '猫',
            '狗', '狗', '狗', '狗', '狗', '狗',
            '狗', '狗',
            
            # 肉类
            '猫狗', '猫狗', '猫狗', '猫狗',
            '猫狗', '猫狗', '猫狗',
            '猫狗', '猫狗',
            '猫狗', '猫狗',
            '猫狗', '猫狗',
            '猫狗', '猫狗',
            
            # 鱼类海鲜
            '猫狗', '猫狗', '猫狗', '猫狗', '猫狗',
            '猫狗', '猫狗', '猫狗', '猫狗',
            
            # 蛋奶类
            '猫狗', '猫狗', '猫狗',
            '猫狗', '猫狗', '猫狗',
            
            # 蔬菜类
            '猫狗', '猫狗', '猫狗', '猫狗', '猫狗', '猫狗',
            '猫狗', '猫狗', '猫狗',
            '猫狗', '猫狗', '猫狗',
            
            # 水果类
            '猫狗', '猫狗', '猫狗', '猫狗', '猫狗', '猫狗',
            
            # 谷物类
            '狗', '猫狗', '猫狗', '猫狗', '狗',
            
            # 营养补充剂
            '猫狗', '猫狗', '猫狗', '猫狗', '猫狗', '猫'
        ],
        '功效': [
            # 猫粮狗粮类
            '日常主食', '日常主食', '幼宠成长', '老年保健', '肾脏健康', '肠胃调理',
            '日常主食', '日常主食', '幼宠成长', '老年保健', '大型犬专用', '小型犬专用',
            '关节健康', '体重控制',
            
            # 肉类
            '高蛋白', '高蛋白', '补铁补血', '补心',
            '高蛋白', '补铁补血', '补心',
            '高蛋白', '补铁补血',
            '高蛋白', '补铁补血',
            '低敏', '低敏',
            '低脂', '低脂',
            
            # 鱼类海鲜
            '美毛护肤', '美毛护肤', '低脂', '美毛', '美毛',
            '补钙', '补微量元素', '补锌', '补蛋白',
            
            # 蛋奶类
            '高蛋白', '高蛋白', '高营养',
            '益生菌', '补钙', '易消化',
            
            # 蔬菜类
            '护眼', '护肠胃', '抗癌', '补铁', '补水', '补水',
            '护肠胃', '能量', '健脾',
            '高纤维', '高纤维', '能量',
            
            # 水果类
            '维生素', '能量', '抗氧化', '维生素', '补水', '助消化',
            
            # 谷物类
            '能量', '高纤维', '易消化', '能量', '能量',
            
            # 营养补充剂
            '美毛护肤', '调理肠胃', '保护关节', '补钙', '提高免疫', '心脏健康'
        ]
    }
    return pd.DataFrame(data)

food_db = load_food_database()

# ========== 营养建议函数 ==========
def get_nutrition_recommendations(total_cal, daily_cal, total_pro, pet_type, pet_age, pet_weight):
    """根据营养缺口推荐补充剂"""
    recommendations = []
    
    # 热量缺口判断
    cal_gap = daily_cal - total_cal
    if cal_gap > 100:
        recommendations.append({
            '类型': '热量不足',
            '建议': '增加主粮份量或添加高热量食物',
            '推荐补充剂': '营养膏、羊奶粉',
            'icon': '🔥'
        })
    elif cal_gap < -100:
        recommendations.append({
            '类型': '热量超标',
            '建议': '减少主粮份量，增加运动量',
            '推荐补充剂': '低卡零食、膳食纤维',
            'icon': '⚠️'
        })
    
    # 蛋白质缺口（按每公斤体重计算）
    pro_need = pet_weight * (5 if pet_type == '猫' else 4.5)
    pro_gap = pro_need - total_pro
    if pro_gap > 5:
        recommendations.append({
            '类型': '蛋白质不足',
            '建议': '添加高蛋白食物',
            '推荐补充剂': '鸡胸肉、鱼肉、蛋白粉',
            'icon': '🥩'
        })
    elif pro_gap < -5:
        recommendations.append({
            '类型': '蛋白质超标',
            '建议': '适当减少高蛋白食物',
            '推荐补充剂': '多喝水帮助代谢',
            'icon': '⚠️'
        })
    
    # 根据年龄推荐
    if pet_age < 1:
        recommendations.append({
            '类型': '幼宠成长',
            '建议': '需要额外钙质和DHA',
            '推荐补充剂': '幼宠钙粉、DHA补充剂',
            'icon': '🐾'
        })
    elif pet_age > 7:
        recommendations.append({
            '类型': '老年保健',
            '建议': '关注关节和心脏健康',
            '推荐补充剂': '软骨素、鱼油、辅酶Q10',
            'icon': '👴'
        })
    
    # 根据宠物类型推荐
    if pet_type == '猫':
        recommendations.append({
            '类型': '猫咪必备',
            '建议': '牛磺酸对猫咪心脏和视力至关重要',
            '推荐补充剂': '牛磺酸补充剂',
            'icon': '🐱'
        })
    else:  # 狗
        # 根据体型推荐
        if pet_weight > 25:
            recommendations.append({
                '类型': '大型犬保健',
                '建议': '关注关节健康',
                '推荐补充剂': '软骨素、葡萄糖胺',
                'icon': '🦴'
            })
        elif pet_weight < 5:
            recommendations.append({
                '类型': '小型犬保健',
                '建议': '注意牙齿和心脏健康',
                '推荐补充剂': '辅酶Q10、洁齿骨',
                'icon': '🐕'
            })
    
    # 如果没有任何推荐，给个默认的
    if len(recommendations) == 0:
        recommendations.append({
            '类型': '营养均衡',
            '建议': '今日营养摄入很均衡，继续保持！',
            '推荐补充剂': '无需额外补充',
            'icon': '✅'
        })
    
    return recommendations

# ========== 饮食计划推荐 ==========
def generate_meal_plan(pet_type, pet_weight, pet_age, activity, preferences=None):
    """生成每日饮食计划推荐"""
    # 计算每日热量需求
    if pet_type == "猫":
        base = pet_weight * 70
    else:
        base = pet_weight * 100
    
    act_factor = {"很少": 0.8, "一般": 1.0, "活泼": 1.2, "很好动": 1.4}
    daily_cal = round(base * act_factor[activity])
    
    # 根据年龄调整
    if pet_age < 1:
        # 幼宠需要多餐
        meal_count = 4
        meal_distribution = [0.25, 0.25, 0.25, 0.25]  # 四餐均分
    elif pet_age > 7:
        # 老年宠少食多餐
        meal_count = 3
        meal_distribution = [0.3, 0.4, 0.3]  # 早中晚
    else:
        # 成年宠两餐
        meal_count = 2
        meal_distribution = [0.4, 0.6]  # 早晚
    
    # 推荐食物
    if pet_type == "猫":
        food_recommendations = {
            '主食': '猫粮（干）',
            '肉类': '鸡胸肉、三文鱼',
            '补充剂': '牛磺酸、鱼油'
        }
    else:
        food_recommendations = {
            '主食': '狗粮（干）',
            '肉类': '鸡胸肉、牛肉',
            '补充剂': '软骨素（大型犬）、益生菌'
        }
    
    # 生成计划
    plan = {
        '每日热量': daily_cal,
        '建议餐数': meal_count,
        '餐次分布': meal_distribution,
        '食物推荐': food_recommendations,
        '说明': []
    }
    
    # 添加说明
    if pet_age < 1:
        plan['说明'].append("🐾 幼宠需要少食多餐，每天4餐有助于消化吸收")
    elif pet_age > 7:
        plan['说明'].append("👴 老年宠物建议增加关节保健品，如软骨素")
    
    if pet_type == "猫":
        plan['说明'].append("🐱 猫咪需要牛磺酸，可添加专门补充剂")
    else:
        if pet_weight > 25:
            plan['说明'].append("🦴 大型犬注意关节保护，建议添加软骨素")
    
    return plan

# 左右布局
left, right = st.columns([1, 2])

# ===== 左边：宠物档案 =====
with left:
    # 宠物选择器
    st.markdown("""
    <div style='background-color: white; border-radius: 15px; padding: 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 1rem;'>
        <h3 style='color: #FF6B6B; margin-top: 0; margin-bottom: 1rem;'>🐾 选择宠物</h3>
    """, unsafe_allow_html=True)
    
    # 获取所有宠物
    pets = get_all_pets()
    pet_options = [f"{p[1]} ({p[2]})" for p in pets]
    pet_ids = [p[0] for p in pets]
    
    selected_pet_id = None
    pet_name = "旺财"
    pet_type = "猫"
    pet_age = 3.0
    pet_weight = 5.0
    
    if len(pets) == 0:
        st.info("还没有宠物，请先添加")
    else:
        # 宠物选择下拉框
        selected_index = st.selectbox(
            "选择宠物",
            range(len(pet_options)),
            format_func=lambda x: pet_options[x],
            key="pet_selector"
        )
        selected_pet_id = pet_ids[selected_index]
        
        # 获取选中宠物的信息
        pet_info = get_pet_info(selected_pet_id)
        if pet_info:
            pet_name = pet_info['pet_name']
            pet_type = pet_info['pet_type']
            # 计算年龄（根据出生日期）
            if pet_info['birth_date']:
                birth = datetime.datetime.strptime(pet_info['birth_date'], '%Y-%m-%d').date()
                today = datetime.datetime.now().date()
                pet_age = (today - birth).days / 365
            else:
                pet_age = 3.0
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 添加新宠物按钮（在折叠框中）
    with st.expander("➕ 添加新宠物"):
        new_name = st.text_input("宠物名字", key="new_pet_name")
        new_type = st.selectbox("类型", ["猫", "狗"], key="new_pet_type")
        new_gender = st.selectbox("性别", ["男生", "女生"], key="new_pet_gender")
        new_birth = st.date_input("出生日期", datetime.date(2023, 1, 1), key="new_pet_birth")
        
        if st.button("添加宠物", use_container_width=True):
            if add_pet(new_name, new_type, new_gender, new_birth.strftime('%Y-%m-%d')):
                st.success(f"✅ 添加成功！")
                st.rerun()
    
    if selected_pet_id:
        st.markdown("""
        <div style='background-color: white; border-radius: 15px; padding: 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 1rem;'>
        """, unsafe_allow_html=True)
        
        # 宠物信息输入
        pet_name = st.text_input("🐾 名字", pet_name, key="pet_name_input")
        col1, col2 = st.columns(2)
        with col1:
            pet_type = st.selectbox("🐱 类型", ["猫", "狗"], index=0 if pet_type=='猫' else 1, key="pet_type_select")
        with col2:
            pet_gender = st.selectbox("⚥ 性别", ["男生", "女生"], key="pet_gender_select")
        
        col1, col2 = st.columns(2)
        with col1:
            pet_age = st.number_input("📅 年龄", 0.0, 30.0, float(pet_age), step=0.5, key="pet_age_input")
        with col2:
            pet_weight = st.number_input("⚖️ 体重", 0.1, 100.0, pet_weight, step=0.1, key="pet_weight_input")
        
        activity = st.select_slider(
            "🏃 活动量",
            options=["很少", "一般", "活泼", "很好动"],
            value="一般",
            key="activity_slider"
        )
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # 计算热量
        if pet_type == "猫":
            base = pet_weight * 70
        else:
            base = pet_weight * 100
        
        act_factor = {"很少": 0.8, "一般": 1.0, "活泼": 1.2, "很好动": 1.4}
        daily_cal = round(base * act_factor[activity])
        
        # 今日目标卡片
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #4ECDC4 0%, #45B7D1 100%); border-radius: 15px; padding: 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 1rem; text-align: center;'>
            <h3 style='color: white; margin-top: 0; margin-bottom: 0.5rem;'>📊 今日目标</h3>
            <div style='font-size: 3rem; font-weight: 700; color: white; line-height: 1.2;'>{daily_cal}</div>
            <div style='font-size: 1rem; color: rgba(255,255,255,0.9);'>千卡</div>
        </div>
        """, unsafe_allow_html=True)
        
        # 饮食计划按钮（折叠框）
        with st.expander("📅 查看今日饮食计划"):
            plan = generate_meal_plan(pet_type, pet_weight, pet_age, activity)
            
            st.markdown(f"""
            <div style='background-color: #F9F9F9; border-radius: 10px; padding: 1rem;'>
                <p><strong>📊 今日推荐</strong></p>
                <p>🔥 总热量：{plan['每日热量']} kcal</p>
                <p>🍽️ 建议餐数：{plan['建议餐数']} 餐</p>
                <p><strong>🥩 推荐食物</strong></p>
                <p>主食：{plan['食物推荐']['主食']}</p>
                <p>肉类：{plan['食物推荐']['肉类']}</p>
                <p>补充剂：{plan['食物推荐']['补充剂']}</p>
            </div>
            """, unsafe_allow_html=True)
            
            for tip in plan['说明']:
                st.info(tip)
        
        # 加载记录按钮
        if st.button("📥 加载今日记录", use_container_width=True):
            with st.spinner("加载中..."):
                records = load_records_from_db(selected_pet_id)
                if records:
                    st.session_state.history = records
                    st.success(f"✅ 已加载 {len(records)} 条记录")
                    st.rerun()
                else:
                    st.info("📭 暂无今日记录")
    else:
        st.info("👆 请先添加宠物")

# ===== 右边：饮食记录 =====
with right:
    st.markdown("""
    <div style='background-color: white; border-radius: 15px; padding: 1rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 1rem;'>
        <h3 style='color: #FF6B6B; margin: 0;'>🍖 今日饮食</h3>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["📸 拍照识别", "📝 手动输入", "📊 今日分析", "📈 历史趋势"])
    
    # ===== 标签页1：拍照识别 =====
    with tab1:
        st.markdown("""
        <div style='background-color: white; border-radius: 15px; padding: 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
            <p style='color: #6C757D; margin-top: 0;'>上传食物照片，AI会自动识别</p>
        """, unsafe_allow_html=True)
        
        pic = st.file_uploader("选择图片", type=["jpg", "png", "jpeg"], help="支持jpg、png、jpeg格式")
        
        if pic and selected_pet_id:
            st.image(pic, width=300, caption="预览")
            
            with st.spinner("🔍 百度AI正在识别中..."):
                pic.seek(0)
                image_data = pic.read()
                
                # 调用百度AI
                result = client_bd.advancedGeneral(image_data)
                
                if 'result' in result and len(result['result']) > 0:
                    top_result = result['result'][0]
                    found = top_result['keyword']
                    confidence = top_result['score'] * 100
                    
                    st.success(f"✅ 识别到：{found} (置信度：{confidence:.1f}%)")
                    
                    if len(result['result']) > 1:
                        with st.expander("其他可能结果"):
                            for item in result['result'][1:]:
                                st.write(f"- {item['keyword']} ({item['score']*100:.1f}%)")
                    
                    # 查找匹配
                    matched_foods = food_db[food_db['食物名称'].str.contains(found, na=False)]
                    if len(matched_foods) > 0:
                        food_info = matched_foods.iloc[0]
                        st.info(f"📌 在数据库中找到：{food_info['食物名称']}")
                    else:
                        st.warning("⚠️ 未找到完全匹配，请手动选择")
                        selected = st.selectbox("请选择最接近的食物", food_db['食物名称'].tolist())
                        food_info = food_db[food_db['食物名称'] == selected].iloc[0]
                else:
                    found = random.choice(["猫粮（干）", "鸡胸肉", "狗粮（干）", "三文鱼"])
                    st.warning("⚠️ 百度AI未识别出结果，使用随机食物")
                    st.success(f"识别到：{found}")
                    food_info = food_db[food_db['食物名称'] == found].iloc[0]
                
                # 输入份量
                col1, col2 = st.columns(2)
                with col1:
                    amount = st.number_input("🥄 吃了多少克？", 10, 300, 50)
                with col2:
                    meal_time = st.selectbox("🍽️ 哪一餐？", ["早餐", "午餐", "晚餐", "加餐"])
                
                # 计算营养
                cal = round(amount * food_info['热量_kcal_100g'] / 100)
                pro = round(amount * food_info['蛋白质_g_100g'] / 100, 1)
                
                # 结果显示
                col1, col2, col3 = st.columns(3)
                col1.metric("🔥 热量", f"{cal} kcal")
                col2.metric("🥩 蛋白质", f"{pro} g")
                col3.metric("⚖️ 份量", f"{amount} g")
                
                if st.button("💾 保存记录", use_container_width=True):
                    record = {
                        'pet_id': selected_pet_id,
                        'food_name': food_info['食物名称'],
                        'amount': amount,
                        'calories': cal,
                        'protein': pro,
                        'meal_time': meal_time
                    }
                    
                    if save_record_to_db(record):
                        display_record = {
                            '时间': datetime.datetime.now().strftime("%H:%M"),
                            '食物': food_info['食物名称'],
                            '热量': cal,
                            '蛋白质': pro
                        }
                        st.session_state.history.append(display_record)
                        st.success("✅ 记录已保存！")
        elif pic and not selected_pet_id:
            st.warning("请先在左边选择或添加宠物")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # ===== 标签页2：手动输入 =====
    with tab2:
        st.markdown("""
        <div style='background-color: white; border-radius: 15px; padding: 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
        """, unsafe_allow_html=True)
        
        if not selected_pet_id:
            st.warning("请先在左边选择或添加宠物")
        else:
            food_list = food_db['食物名称'].tolist()
            chosen = st.selectbox("🥘 选择食物", food_list)
            
            food_info = food_db[food_db['食物名称'] == chosen].iloc[0]
            
            # 显示营养信息
            st.markdown(f"""
            <div style='background-color: #F8F9FA; border-radius: 10px; padding: 1rem; margin: 1rem 0;'>
                <p><strong>📊 营养信息（每100g）</strong></p>
                <p>🔥 热量：{food_info['热量_kcal_100g']} kcal</p>
                <p>🥩 蛋白质：{food_info['蛋白质_g_100g']} g</p>
                <p>🫧 脂肪：{food_info['脂肪_g_100g']} g</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                amount = st.slider("🥄 份量(克)", 10, 300, 50)
            with col2:
                meal_time = st.selectbox("🍽️ 哪一餐？", ["早餐", "午餐", "晚餐", "加餐"], key="manual_meal")
            
            cal = round(amount * food_info['热量_kcal_100g'] / 100)
            pro = round(amount * food_info['蛋白质_g_100g'] / 100, 1)
            
            col1, col2 = st.columns(2)
            col1.metric("🔥 热量", f"{cal} kcal")
            col2.metric("🥩 蛋白质", f"{pro} g")
            
            if st.button("💾 保存记录", key="save_manual", use_container_width=True):
                record = {
                    'pet_id': selected_pet_id,
                    'food_name': chosen,
                    'amount': amount,
                    'calories': cal,
                    'protein': pro,
                    'meal_time': meal_time
                }
                
                if save_record_to_db(record):
                    display_record = {
                        '时间': datetime.datetime.now().strftime("%H:%M"),
                        '食物': chosen,
                        '热量': cal,
                        '蛋白质': pro
                    }
                    st.session_state.history.append(display_record)
                    st.success("✅ 记录已保存！")
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # ===== 标签页3：今日分析 =====
    with tab3:
        st.markdown("""
        <div style='background-color: white; border-radius: 15px; padding: 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
        """, unsafe_allow_html=True)
        
        if not selected_pet_id:
            st.warning("请先在左边选择或添加宠物")
        elif len(st.session_state.history) == 0:
            st.info("📭 今天还没有记录，快去添加吧！")
        else:
            total_cal = sum([x['热量'] for x in st.session_state.history])
            total_pro = sum([x['蛋白质'] for x in st.session_state.history])
            
            # 进度卡片
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div style='text-align: center;'>
                    <p style='color: #6C757D; margin-bottom: 0;'>🔥 热量进度</p>
                    <p style='font-size: 2rem; font-weight: 700; color: #4ECDC4; margin: 0;'>{total_cal}/{daily_cal}</p>
                    <p style='color: #6C757D;'>kcal</p>
                </div>
                """, unsafe_allow_html=True)
                st.progress(min(1.0, total_cal/daily_cal))
            
            with col2:
                st.markdown(f"""
                <div style='text-align: center;'>
                    <p style='color: #6C757D; margin-bottom: 0;'>🥩 蛋白质</p>
                    <p style='font-size: 2rem; font-weight: 700; color: #FF6B6B; margin: 0;'>{total_pro}g</p>
                    <p style='color: #6C757D;'>今日摄入</p>
                </div>
                """, unsafe_allow_html=True)
            
            # 获取营养建议
            recommendations = get_nutrition_recommendations(
                total_cal, daily_cal, total_pro, pet_type, pet_age, pet_weight
            )
            
            # 显示营养建议卡片
            st.markdown("### 💡 今日营养建议")
            
            # 创建两列布局显示建议
            cols = st.columns(len(recommendations))
            for i, rec in enumerate(recommendations):
                with cols[i]:
                    st.markdown(f"""
                    <div style='background-color: #F0F8FF; border-radius: 10px; padding: 1rem; text-align: center; height: 100%;'>
                        <div style='font-size: 2rem;'>{rec['icon']}</div>
                        <h4 style='color: #4ECDC4; margin: 0.5rem 0;'>{rec['类型']}</h4>
                        <p style='font-size: 0.9rem; margin: 0.3rem 0;'>{rec['建议']}</p>
                        <p style='font-size: 0.9rem; font-weight: bold; color: #FF6B6B; margin: 0.3rem 0;'>{rec['推荐补充剂']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # 传统提示作为补充
            st.markdown("---")
            if total_cal < daily_cal * 0.7:
                st.info("📉 热量摄入不足70%，建议加餐")
            elif total_cal > daily_cal * 1.1:
                st.warning("📈 热量超标110%，注意控制")
            else:
                st.success("📊 热量摄入在理想范围")
            
            # 详细记录
            st.markdown("---")
            st.markdown("### 📝 详细记录")
            for i, r in enumerate(st.session_state.history):
                st.markdown(f"""
                <div style='background-color: #F8F9FA; border-radius: 10px; padding: 0.5rem 1rem; margin: 0.5rem 0; display: flex; justify-content: space-between;'>
                    <span>🕒 {r['时间']}</span>
                    <span>🍖 {r['食物']}</span>
                    <span>🔥 {r['热量']}kcal</span>
                </div>
                """, unsafe_allow_html=True)
            
            if st.button("🗑️ 清空记录", use_container_width=True):
                st.session_state.history = []
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # ===== 标签页4：历史趋势 =====
    with tab4:
        st.markdown("""
        <div style='background-color: white; border-radius: 15px; padding: 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
        """, unsafe_allow_html=True)
        
        if not selected_pet_id:
            st.warning("请先在左边选择或添加宠物")
        else:
            # 时间范围选择
            time_range = st.radio(
                "选择时间范围",
                ["近7天", "近30天", "近90天"],
                horizontal=True,
                key="time_range"
            )
            
            days = 7
            if time_range == "近30天":
                days = 30
            elif time_range == "近90天":
                days = 90
            
            # 加载历史数据
            history_data = load_history_records(selected_pet_id, days)
            
            if len(history_data) == 0:
                st.info("📊 暂无历史数据")
            else:
                # 转换成DataFrame
                df = pd.DataFrame(history_data)
                
                # 热量趋势图
                st.markdown("#### 🔥 每日热量摄入趋势")
                fig_cal = px.line(
                    df, 
                    x='日期', 
                    y='总热量',
                    markers=True,
                    title=f'过去{len(df)}天热量摄入',
                    labels={'总热量': '热量 (kcal)', '日期': '日期'}
                )
                fig_cal.add_hline(
                    y=daily_cal, 
                    line_dash="dash", 
                    line_color="red",
                    annotation_text="每日目标"
                )
                st.plotly_chart(fig_cal, use_container_width=True)
                
                # 双轴图：热量和蛋白质
                st.markdown("#### 📊 热量与蛋白质对比")
                fig2 = go.Figure()
                fig2.add_trace(go.Bar(
                    x=df['日期'],
                    y=df['总热量'],
                    name='热量 (kcal)',
                    marker_color='#4ECDC4'
                ))
                fig2.add_trace(go.Scatter(
                    x=df['日期'],
                    y=df['总蛋白质'],
                    name='蛋白质 (g)',
                    yaxis='y2',
                    line=dict(color='#FF6B6B', width=3),
                    mode='lines+markers'
                ))
                fig2.update_layout(
                    title='每日热量与蛋白质摄入',
                    xaxis=dict(title='日期'),
                    yaxis=dict(title='热量 (kcal)', color='#4ECDC4'),
                    yaxis2=dict(
                        title='蛋白质 (g)',
                        color='#FF6B6B',
                        overlaying='y',
                        side='right'
                    ),
                    legend=dict(x=0, y=1.1)
                )
                st.plotly_chart(fig2, use_container_width=True)
                
                # 统计摘要
                st.markdown("#### 📋 统计摘要")
                col1, col2, col3 = st.columns(3)
                with col1:
                    avg_cal = df['总热量'].mean()
                    st.metric("平均每日热量", f"{avg_cal:.0f} kcal")
                with col2:
                    avg_pro = df['总蛋白质'].mean()
                    st.metric("平均每日蛋白质", f"{avg_pro:.1f} g")
                with col3:
                    total_meals = df['餐数'].sum()
                    st.metric("总记录餐数", f"{total_meals} 餐")
                
                # 达标率
                达标天数 = len(df[df['总热量'] >= daily_cal * 0.9])
                达标率 = (达标天数 / len(df)) * 100
                
                st.markdown(f"""
                <div style='background-color: #F0F8FF; border-radius: 10px; padding: 1rem; margin-top: 1rem;'>
                    <p><strong>🎯 达标率</strong>：{达标率:.1f}% ({达标天数}/{len(df)}天 达到目标90%以上)</p>
                    <div style='background-color: #E0E0E0; border-radius: 5px; height: 10px; width: 100%;'>
                        <div style='background-color: #4ECDC4; border-radius: 5px; height: 10px; width: {达标率}%;'></div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

# 底部版权
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #6C757D; font-size: 0.9rem; padding: 1rem;'>
    🐾 宠物AI营养师 · 让毛孩子吃得健康 · 版本 3.0（多宠物+图表+饮食计划）
</div>
""", unsafe_allow_html=True)
