import streamlit as st
import pandas as pd
import datetime
import random
from aip import AipImageClassify  # 百度AI的SDK

# 百度AI配置（已配置好你的密钥）
APP_ID = '122401445'
API_KEY = 's0Ci5vaSBEYA1VT4Ez9jH5j6'
SECRET_KEY = '9yqsGkNOXopZpsDNPKmauO7kaNn5p1nc'

# 初始化百度AI客户端
client = AipImageClassify(APP_ID, API_KEY, SECRET_KEY)

# 页面设置
st.set_page_config(
    page_title="宠物AI营养师", 
    page_icon="🐱",
    layout="wide"
)

# 标题
st.title("🐱 宠物AI营养师")
st.markdown("---")

# 初始化历史记录
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
    st.header("📋 宠物档案")
    
    pet_name = st.text_input("名字", "旺财")
    
    col1, col2 = st.columns(2)
    with col1:
        pet_type = st.selectbox("类型", ["猫", "狗"])
    with col2:
        pet_age = st.number_input("年龄", 0.0, 30.0, 3.0)
    
    pet_weight = st.number_input("体重(公斤)", 0.1, 100.0, 5.0)
    
    activity = st.select_slider("活动量", ["很少", "一般", "活泼", "很好动"], "一般")
    
    # 计算热量
    if pet_type == "猫":
        base = pet_weight * 70
    else:
        base = pet_weight * 100
    
    act_factor = {"很少": 0.8, "一般": 1.0, "活泼": 1.2, "很好动": 1.4}
    daily_cal = round(base * act_factor[activity])
    
    st.markdown("---")
    st.subheader("📊 今日目标")
    st.markdown(f"<h2 style='text-align:center'>{daily_cal} kcal</h2>", unsafe_allow_html=True)

# ===== 右边：饮食记录 =====
with right:
    st.header("🍖 今日饮食")
    
    tab1, tab2, tab3 = st.tabs(["📸 拍照", "📝 手动", "📊 分析"])
    
    # 标签页1：拍照（真AI识别）
    with tab1:
        st.write("上传食物照片，百度AI自动识别")
        pic = st.file_uploader("选择图片", type=["jpg", "png", "jpeg"])
        
        if pic:
            st.image(pic, width=250)
            
            # 调用百度AI真实识别
            with st.spinner("🔍 百度AI正在识别中..."):
                # 读取图片数据
                pic.seek(0)
                image_data = pic.read()
                
                # 调用百度AI的通用物体识别接口
                result = client.advancedGeneral(image_data)
                
                # 解析结果
                if 'result' in result and len(result['result']) > 0:
                    # 取识别结果中置信度最高的
                    top_result = result['result'][0]
                    found = top_result['keyword']
                    confidence = top_result['score'] * 100
                    
                    st.success(f"✅ 识别到：{found} (置信度：{confidence:.1f}%)")
                    
                    # 显示更多识别结果
                    if len(result['result']) > 1:
                        with st.expander("其他可能结果"):
                            for item in result['result'][1:]:
                                st.write(f"- {item['keyword']} ({item['score']*100:.1f}%)")
                    
                    # 在数据库中查找匹配的食物
                    matched_foods = food_db[food_db['食物名称'].str.contains(found, na=False)]
                    if len(matched_foods) > 0:
                        food_info = matched_foods.iloc[0]
                        st.info(f"在数据库中找到匹配：{food_info['食物名称']}")
                    else:
                        # 没找到匹配，让用户选择
                        st.warning("未在数据库中找到完全匹配的食物，请手动选择")
                        selected = st.selectbox("请选择最接近的食物", food_db['食物名称'].tolist())
                        food_info = food_db[food_db['食物名称'] == selected].iloc[0]
                else:
                    found = random.choice(["猫粮（干）", "鸡胸肉", "狗粮（干）", "三文鱼"])
                    st.warning("⚠️ 百度AI未识别出结果，使用随机食物替代")
                    st.success(f"识别到：{found}")
                    food_info = food_db[food_db['食物名称'] == found].iloc[0]
                
                # 输入份量
                amount = st.number_input("吃了多少克？", 10, 300, 50)
                
                # 计算营养
                cal = round(amount * food_info['热量_kcal_100g'] / 100)
                pro = round(amount * food_info['蛋白质_g_100g'] / 100, 1)
                
                st.metric("热量", f"{cal} kcal")
                st.metric("蛋白质", f"{pro} g")
                
                if st.button("保存记录"):
                    record = {
                        '时间': datetime.datetime.now().strftime("%H:%M"),
                        '食物': food_info['食物名称'],
                        '热量': cal,
                        '蛋白质': pro
                    }
                    st.session_state.history.append(record)
                    st.success("已保存")
    
    # 标签页2：手动
    with tab2:
        st.write("手动选择食物")
        
        food_list = food_db['食物名称'].tolist()
        chosen = st.selectbox("选择食物", food_list)
        
        food_info = food_db[food_db['食物名称'] == chosen].iloc[0]
        
        st.write(f"每100g：{food_info['热量_kcal_100g']} kcal")
        
        amount = st.slider("份量(克)", 10, 300, 50, key="manual_slider")
        
        cal = round(amount * food_info['热量_kcal_100g'] / 100)
        pro = round(amount * food_info['蛋白质_g_100g'] / 100, 1)
        
        st.metric("热量", f"{cal} kcal")
        st.metric("蛋白质", f"{pro} g")
        
        if st.button("保存", key="save_manual"):
            record = {
                '时间': datetime.datetime.now().strftime("%H:%M"),
                '食物': chosen,
                '热量': cal,
                '蛋白质': pro
            }
            st.session_state.history.append(record)
            st.success("已保存")
    
    # 标签页3：分析
    with tab3:
        st.write("今日汇总")
        
        if len(st.session_state.history) == 0:
            st.info("还没有记录")
        else:
            total_cal = sum([x['热量'] for x in st.session_state.history])
            total_pro = sum([x['蛋白质'] for x in st.session_state.history])
            
            col1, col2 = st.columns(2)
            col1.metric("总热量", f"{total_cal} / {daily_cal} kcal")
            col2.metric("总蛋白质", f"{total_pro} g")
            
            st.progress(min(1.0, total_cal/daily_cal))
            
            # 智能提示
            if total_cal < daily_cal * 0.7:
                st.info("💡 吃得有点少，再吃点吧")
            elif total_cal > daily_cal * 1.1:
                st.warning("⚠️ 热量超标了，明天注意控制")
            else:
                st.success("👍 热量刚刚好")
            
            st.write("详细记录：")
            for r in st.session_state.history:
                st.write(f"{r['时间']} - {r['食物']} - {r['热量']}kcal")
            
            if st.button("清空"):
                st.session_state.history = []
                st.rerun()