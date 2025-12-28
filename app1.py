import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd  # 用于处理历史记录表格
from core_functions import user_register, user_login, predict_match, get_prediction_history

# 页面配置
st.set_page_config(
    page_title="英雄联盟对局胜胜率预测系统",
    page_icon="🎮",
    layout="wide"
)

# 初始化会话状态
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
if "username" not in st.session_state:
    st.session_state["username"] = ""

# 未登录状态
if st.session_state["user_id"] is None:
    st.title("🎮 英雄联盟对局胜率预测系统")
    tab1, tab2 = st.tabs(["登录", "注册"])
    
    # 登录标签页
    with tab1:
        st.subheader("用户登录")
        username = st.text_input("用户名", key="login_name")
        password = st.text_input("密码", type="password", key="login_pwd")
        login_btn = st.button("登录")
        
        if login_btn:
            if not username or not password:
                st.error("用户名和密码不能为空！")
            else:
                success, msg = user_login(username, password)
                if success:
                    st.session_state["user_id"] = msg
                    st.session_state["username"] = username
                    st.success("登录成功！正在刷新页面...")
                    st.rerun()
                else:
                    st.error(msg)
    
    # 注册标签页
    with tab2:
        st.subheader("用户注册")
        new_username = st.text_input("新用户名", key="reg_name")
        new_password = st.text_input("新密码", type="password", key="reg_pwd")
        confirm_pwd = st.text_input("确认密码", type="password", key="reg_confirm")
        reg_btn = st.button("注册")
        
        if reg_btn:
            if not new_username or not new_password:
                st.error("用户名和密码不能为空！")
            elif new_password != confirm_pwd:
                st.error("两次输入的密码不一致！")
            else:
                success, msg = user_register(new_username, new_password)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)

# 已登录状态
else:
    st.title("🎮 英雄联盟对局胜率预测系统")
    st.subheader(f"欢迎回来，{st.session_state['username']}！")
    
    # 退出登录按钮
    if st.button("退出登录"):
        st.session_state["user_id"] = None
        st.session_state["username"] = ""
        st.success("退出成功！正在刷新页面...")
        st.rerun()
    
    # 分栏：左侧输入，右侧结果
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        st.subheader("📝 对局数据输入")
        # 分类特征选择
        firstBlood = st.selectbox("一血归属", ["蓝方", "红方", "无"], key="fb")
        firstTower = st.selectbox("首座防御塔归属", ["蓝方", "红方", "无"], key="ft")
        firstInhibitor = st.selectbox("首座召唤水晶归属", ["蓝方", "红方", "无"], key="fi")
        firstBaron = st.selectbox("首个男爵归属", ["蓝方", "红方", "无"], key="fb_b")
        firstDragon = st.selectbox("首只小龙归属", ["蓝方", "红方", "无"], key="fd")
        firstRiftHerald = st.selectbox("首峡谷先锋归属", ["蓝方", "红方", "无"], key="frh")
        
        # 数值特征滑块
        st.divider()
        st.subheader("📊 资源差值（蓝方-红方）")
        tower_diff = st.slider("防御塔差值", -10, 10, 0, key="tower")
        inhibitor_diff = st.slider("召唤水晶差值", -5, 5, 0, key="inhibitor")
        baron_diff = st.slider("男爵差值", -3, 3, 0, key="baron")
        dragon_diff = st.slider("小龙差值", -5, 5, 0, key="dragon")
        herald_diff = st.slider("峡谷先锋差值", -3, 3, 0, key="herald")
        
        # 预测按钮
        predict_btn = st.button("🚀 开始预测", type="primary")
    
    with col2:
        st.header("📊 预测结果")
        if predict_btn:
            # 调用预测函数
            success, result = predict_match(
                user_id=st.session_state["user_id"],
                firstBlood=firstBlood,
                firstTower=firstTower,
                firstInhibitor=firstInhibitor,
                firstBaron=firstBaron,
                firstDragon=firstDragon,
                firstRiftHerald=firstRiftHerald,
                tower_diff=tower_diff,
                inhibitor_diff=inhibitor_diff,
                baron_diff=baron_diff,
                dragon_diff=dragon_diff,
                herald_diff=herald_diff
            )
            if success:
                # 双方胜率详情（在上）
                st.subheader("双方胜率详情")
                rate_col1, rate_col2 = st.columns(2)
                with rate_col1:
                    st.metric("🔵 蓝方胜率", f"{result['blue_win_prob']:.1%}")
                with rate_col2:
                    st.metric("🔴 红方胜率", f"{1 - result['blue_win_prob']:.1%}")
                
                st.info(f"对局ID: {result['match_id']}")
                st.divider()
                
                # 胜率分布饼图（在下）
                st.subheader("胜率分布饼图")
                # 解决中文乱码
                plt.rcParams['font.sans-serif'] = ['SimHei', 'PingFang SC', 'DejaVu Sans']
                plt.rcParams['axes.unicode_minus'] = False
                
                fig, ax = plt.subplots(figsize=(6, 6))
                labels = ["蓝方", "红方"]
                sizes = [result['blue_win_prob'], 1 - result['blue_win_prob']]
                colors = ['#ADD8E6', '#FFB6C1']  # 淡蓝、淡红
                explode = (0.05, 0.05)  # 饼块突出
                
                ax.pie(
                    sizes,
                    labels=labels,
                    colors=colors,
                    explode=explode,
                    autopct='',
                    startangle=90,
                    shadow=True,
                    labeldistance=1.1
                )

                
                ax.set_title("蓝红方胜率分布", fontsize=14, pad=20, fontweight='bold')
                ax.axis('equal')
                st.pyplot(fig)
            
            else:
                st.error(result)
    
    # 预测历史记录（只显示到预测时间，字段中文）
    st.divider()
    st.subheader("📜 预测历史记录")
    history_btn = st.button("查询历史")
    if history_btn:
        success, history = get_prediction_history(st.session_state["user_id"])
        if success:
            if history:
                # 筛选字段+重命名为中文+格式化胜率
                history_df = pd.DataFrame(history)[[
                    "result_id", "match_id", "blue_win_prob", "predict_time"
                ]].rename(columns={
                    "result_id": "记录ID",
                    "match_id": "对局ID",
                    "blue_win_prob": "蓝方胜率",
                    "predict_time": "预测时间"
                })

                history_df["红方胜率"] = 1 - history_df["蓝方胜率"]
                
                history_df["蓝方胜率"] = history_df["蓝方胜率"].apply(lambda x: f"{x:.1%}")
                history_df["红方胜率"] = history_df["红方胜率"].apply(lambda x: f"{x:.1%}")
                st.dataframe(history_df, use_container_width=True)
            else:
                st.info("暂无预测记录")
        else:
            st.error(history)
