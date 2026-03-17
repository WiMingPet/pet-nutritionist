import streamlit as st
import pandas as pd
import datetime
import random
import os
import sqlite3
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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS diet_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            pet_name TEXT NOT NULL,
            food_name TEXT NOT NULL,
            amount INTEGER NOT NULL,
            calories INTEGER NOT NULL,
            protein REAL NOT NULL,
            meal_time TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_record_to_db(record):
    """保存记录到本地SQLite数据库"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO diet_records (pet_name, food_name, amount, calories, protein, meal_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            record['pet_name'],
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

def load_records_from_db(pet_name):
    """从本地数据库加载今天的记录"""
    try:
        # 获取今天的日期
        today = datetime.datetime.now().date()
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT strftime('%H:%M', created_at), food_name, calories, protein
            FROM diet_records
            WHERE pet_name = ? AND date(created_at) = date(?)
            ORDER BY created_at
        ''', (pet_name, today.isoformat()))
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

# 初始化数据库
init_database()

# 初始化会话状态
if 'history' not in st.session_state:
    st.session_state.history = []

# 食物数据库
@st.cache_data
def load_food_database():
    data = {
        '食物名称': ['猫粮（干）', '猫粮（湿）', '狗粮（干）', '狗粮（湿）', '鸡胸肉', '牛肉', '三文鱼', '鸡蛋', '胡萝卜', '南瓜', '西兰花', '米饭'],
        '类型': ['猫粮', '猫粮', '狗粮', '狗粮', '肉类', '肉类', '鱼类', '蛋类', '蔬菜', '蔬菜', '蔬菜', '谷物'],
        '热量_kcal_100g': [380, 120, 360, 110, 165, 250, 208, 155, 41, 26, 34, 130],
        '蛋白质_g_100g': [30, 8, 25, 7, 31, 26, 20, 13, 0.9, 1, 2.8, 2.7],
        '脂肪_g_100g': [15, 5, 12, 4, 3.6, 17, 13, 11, 0.2, 0.1, 0.4, 0.3]
    }
    return pd.DataFrame(data)

food_db = load_food_database()

# 左右布局
left, right = st.columns([1, 2])

# ===== 左边：宠物档案 =====
with left:
    st.markdown("""
    <div style='background-color: white; border-radius: 15px; padding: 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 1rem;'>
        <h3 style='color: #FF6B6B; margin-top: 0;'>📋 宠物档案</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style='background-color: white; border-radius: 15px; padding: 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 1rem;'>
    """, unsafe_allow_html=True)
    
    pet_name = st.text_input("🐾 名字", "旺财", help="输入你家宝贝的名字")
    
    col1, col2 = st.columns(2)
    with col1:
        pet_type = st.selectbox("🐱 类型", ["猫", "狗"], help="选择宠物类型")
    with col2:
        pet_gender = st.selectbox("⚥ 性别", ["男生", "女生"], help="选择宠物性别")
    
    col1, col2 = st.columns(2)
    with col1:
        pet_age = st.number_input("📅 年龄", 0.0, 30.0, 3.0, step=0.5, help="单位：岁")
    with col2:
        pet_weight = st.number_input("⚖️ 体重", 0.1, 100.0, 5.0, step=0.1, help="单位：公斤")
    
    activity = st.select_slider(
        "🏃 活动量",
        options=["很少", "一般", "活泼", "很好动"],
        value="一般",
        help="选择宠物的日常活动量"
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
    
    # 加载记录按钮
    if st.button("📥 加载今日记录", use_container_width=True):
        with st.spinner("加载中..."):
            records = load_records_from_db(pet_name)
            if records:
                st.session_state.history = records
                st.success(f"✅ 已加载 {len(records)} 条记录")
                st.rerun()
            else:
                st.info("📭 暂无今日记录")

# ===== 右边：饮食记录 =====
with right:
    st.markdown("""
    <div style='background-color: white; border-radius: 15px; padding: 1rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 1rem;'>
        <h3 style='color: #FF6B6B; margin: 0;'>🍖 今日饮食</h3>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["📸 拍照识别", "📝 手动输入", "📊 营养分析"])
    
    # ===== 标签页1：拍照识别 =====
    with tab1:
        st.markdown("""
        <div style='background-color: white; border-radius: 15px; padding: 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
            <p style='color: #6C757D; margin-top: 0;'>上传食物照片，AI会自动识别</p>
        """, unsafe_allow_html=True)
        
        pic = st.file_uploader("选择图片", type=["jpg", "png", "jpeg"], help="支持jpg、png、jpeg格式")
        
        if pic:
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
                        'pet_name': pet_name,
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
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # ===== 标签页2：手动输入 =====
    with tab2:
        st.markdown("""
        <div style='background-color: white; border-radius: 15px; padding: 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
        """, unsafe_allow_html=True)
        
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
                'pet_name': pet_name,
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
    
    # ===== 标签页3：营养分析 =====
    with tab3:
        st.markdown("""
        <div style='background-color: white; border-radius: 15px; padding: 1.5rem; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
        """, unsafe_allow_html=True)
        
        if len(st.session_state.history) == 0:
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
            
            # 智能提示
            if total_cal < daily_cal * 0.7:
                st.info("💡 吃得有点少，再吃点吧")
            elif total_cal > daily_cal * 1.1:
                st.warning("⚠️ 热量超标了，明天注意控制")
            else:
                st.success("👍 热量刚刚好")
            
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

# 底部版权
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #6C757D; font-size: 0.9rem; padding: 1rem;'>
    🐾 宠物AI营养师 · 让毛孩子吃得健康 · 版本 2.0
</div>
""", unsafe_allow_html=True)
