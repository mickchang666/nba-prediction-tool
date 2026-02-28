import streamlit as st
from nba_api.stats.endpoints import leaguegamefinder
from nba_api.stats.static import teams
from datetime import datetime, timedelta
import pandas as pd

# --- 介面設定 ---
st.set_page_config(page_title="NBA 巔峰勝率 AI", page_icon="🏀")
st.title("🏀 NBA 巔峰對決：極簡預測器 v2.0")
st.info("💡 系統已自動整合：近期戰績 + 主場優勢 + 背靠背體力修正")

# 獲取球隊資訊
nba_teams = teams.get_teams()
team_names = [t['full_name'] for t in nba_teams]

# --- 核心邏輯函數 ---
def get_team_data(team_name):
    team_id = [t['id'] for t in nba_teams if t['full_name'] == team_name][0]
    finder = leaguegamefinder.LeagueGameFinder(team_id_nullable=team_id)
    df = finder.get_data_frames()[0]
    df['GAME_DATE'] = pd.to_datetime(df['GAME_DATE'])
    
    # 1. 計算最近 10 場勝率
    recent_10 = df.head(10)
    win_rate = (recent_10['WL'] == 'W').mean()
    
    # 2. 偵測是否為「背靠背 (B2B)」
    # 檢查上一場比賽日期與「今天」的差距
    last_game_date = df.iloc[0]['GAME_DATE']
    is_b2b = (datetime.now() - last_game_date).days <= 1
    
    return win_rate, is_b2b

# --- 網頁佈局 ---
col1, col2 = st.columns(2)
with col1:
    h_name = st.selectbox("🏠 主場球隊", team_names, index=13) # 預設湖人
with col2:
    a_name = st.selectbox("🚌 客場球隊", team_names, index=9)  # 預設勇士

if st.button("⚖️ 執行深度勝率分析"):
    h_wr, h_b2b = get_team_data(h_name)
    a_wr, a_b2b = get_team_data(a_name)
    
    # --- 勝率計分算法 ---
    # 基礎分 (勝率) + 主場優勢 (+0.05) - B2B 懲罰 (-0.08)
    h_score = h_wr + 0.05 - (0.08 if h_b2b else 0)
    a_score = a_wr - (0.08 if a_b2b else 0)
    
    # 轉化為百分比
    total_score = h_score + a_score
    h_prob = h_score / total_score
    a_prob = a_score / total_score

    # --- 顯示結果 ---
    st.markdown("---")
    res_col1, res_col2 = st.columns(2)
    
    with res_col1:
        st.metric(f"{h_name}", f"{h_prob:.1%}")
        if h_b2b: st.error("⚠️ 背靠背作戰 (體力堪憂)")
        else: st.success("✅ 休息充足")
        
    with res_col2:
        st.metric(f"{a_name}", f"{a_prob:.1%}")
        if a_b2b: st.error("⚠️ 背靠背作戰 (體力堪憂)")
        else: st.success("✅ 休息充足")

    # --- 最終下注建議 ---
    diff = abs(h_prob - a_prob)
    recommend = h_name if h_prob > a_prob else a_name
    
    st.markdown("### 🎯 最終預測建議")
    if diff > 0.15:
        st.success(f"推薦下注：**{recommend}** (勝率優勢顯著，建議信心投注)")
    elif diff > 0.05:
        st.info(f"推薦下注：**{recommend}** (略佔優勢，建議小注)")
    else:

        st.warning("雙方勢均力敵，建議觀望或選擇「大分/小分」盤口。")
