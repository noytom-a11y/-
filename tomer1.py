# ====================================================
# tomer1.py - קובץ ממשק Streamlit (מפת צ'אקרות ענק יציבה, עדכון סופי)
# ====================================================
import streamlit as st
import pandas as pd
from datetime import datetime
import re

# *** הייבוא הקריטי: ייבוא כל הפונקציות והקבועים הדרושים ***
from tomer import run_numerology_tool_for_app, ALL_MASTER_NUMBERS, KARMIC_NUMBERS

# --- פונקציות צביעה ועיצוב ---

# צבעי העיצוב הסופיים
COLOR_MAP = {
    '⭐ תדר מאסטר': '#DC143C',     # אדום (MASTER)
    '⚠️ תדר חלש/מעכב': '#0000FF',  # כחול (WEAK: 2, 7)
    '❌ תדר קארמתי': '#A9A9A9',    # אפור (KARMIC: 13, 14, 16, 19)
    '✅ תדר חזק': '#FFFF00',       # צהוב (STRONG)
    '➖ תדר מאוזן': '#F0F2F6',     # אפור בהיר (MEDIUM/NEUTRAL)
    '⚪ אתגר חזק במיוחד': '#C0C0C0' # אפור מתכתי
}


def style_cycles_table(df, df_full_data):
    """
    🚨 תוקן: צובעת את התאים בטבלת מחזורי החיים לפי מפת הצבעים החדשה.
    """
    
    master_style = f'background-color: {COLOR_MAP["⭐ תדר מאסטר"]}; color: white; font-weight: bold;'
    karmic_style = f'background-color: {COLOR_MAP["❌ תדר קארמתי"]}; color: white;' 
    strong_blue_style = f'background-color: {COLOR_MAP["⚠️ תדר חלש/מעכב"]}; color: white;' 
    strong_yellow_style = f'background-color: {COLOR_MAP["✅ תדר חזק"]}; color: black;' 
    default_style = ''

    df_style = pd.DataFrame(default_style, index=df.index, columns=df.columns)
    p_freq_col = 'משאל"ה/שיא (תדר+עוצמה)'
    w_freq_col = 'אתגר (תדר+עוצמה)'
    
    STRONG_NUMBERS = {1, 5, 8, 9} 
    
    # --- צביעת משאל"ה/שיא (Primary Cycle) ---
    master_mask_p = df_full_data['__משאלה_נקי'].isin(ALL_MASTER_NUMBERS)
    karmic_mask_p = df_full_data['__משאלה_נקי'].isin(KARMIC_NUMBERS) 
    strong_mask_p = (~master_mask_p) & (~karmic_mask_p) & (df_full_data['__משאלה_נקי'].isin(STRONG_NUMBERS))
    
    df_style.loc[karmic_mask_p, p_freq_col] = karmic_style 
    df_style.loc[master_mask_p, p_freq_col] = master_style 
    df_style.loc[strong_mask_p, p_freq_col] = strong_yellow_style 

    # --- צביעת אתגר (Challenge/W) ---
    zero_mask_w = df_full_data['__אתגר_נקי'] == 0 
    strong_mask_w = df_full_data['__אתגר_נקי'].isin(STRONG_NUMBERS)
    weak_mask_w = df_full_data['__אתגר_נקי'].isin({2, 7})
    
    df_style.loc[zero_mask_w, w_freq_col] = master_style # אדום לאתגר 0 (חזק במיוחד)
    df_style.loc[strong_mask_w, w_freq_col] = strong_yellow_style
    df_style.loc[weak_mask_w, w_freq_col] = strong_blue_style
    
    return df_style

def highlight_chakras(s):
    """צובעת שורה שלמה בטבלת הצ'אקרות לפי הכללים החדשים."""
    
    strength_text = s['אפיון']
    
    is_master = '⭐ תדר מאסטר' in strength_text
    is_karmic = '❌ תדר קארמתי' in strength_text
    is_strong = '✅ תדר חזק' in strength_text
    is_weak = '⚠️ תדר חלש/מעכב' in strength_text
    
    style = COLOR_MAP['➖ תדר מאוזן']
    
    if is_master:
        style = COLOR_MAP['⭐ תדר מאסטר']
    elif is_karmic:
        style = COLOR_MAP['❌ תדר קארמתי']
    elif is_weak: 
        style = COLOR_MAP['⚠️ תדר חלש/מעכב']
    elif is_strong:
        style = COLOR_MAP['✅ תדר חזק']
        
    # צבע טקסט לבן עבור רקעים כהים
    text_color = 'white' if style in ['#A9A9A9', '#DC143C', '#0000FF'] else 'black'
    
    # הוספת הדגשה לכל הפונטים בשורה
    return [f'background-color: {style}; color: {text_color}; font-weight: bold;'] * len(s)


def extract_numeric_value(df, col_name):
    """מחלץ רק את הערך המספרי מהעמודה, תוך שמירה על המבנה של הטבלה."""
    # משתמשים בעמודה הנקייה '__אתגר_נקי' שהוחזרה מהלוגיקה
    return df['__אתגר_נקי']

def main():
    
    st.set_page_config(
        page_title="נומרולוגית הצ'אקרות ומחזורי החיים", 
        layout="wide", 
        initial_sidebar_state="expanded"
    )
    
    # CSS מותאם אישית ל-RTL ולמרכוז
    st.markdown("""
        <style>
        /* הגדרת כיוון כללי מימין לשמאל */
        div.stApp { direction: rtl; }
        h1, h2, h3 { text-align: right; }
        
        /* מגביל את רוחב הצ'אקרות ל-90% וממרכז את המיכל */
        .chakra-table-container {
            max-width: 90%; 
            margin: 0 auto;
        }
        
        /* הגדלת גובה שורה ויישור כללי */
        .stDataFrame table, .stDataFrame th, .stDataFrame td {
            text-align: center !important; 
            vertical-align: middle !important;
            font-size: 1.5em; /* הגדלת פונט כללית לכל הטקסט (צ'אקרה + אפיון) */
            height: 200px; /* הגדלת גובה השורות כדי ליצור מפה אנכית */
        }

        /* הגדלת גודל הפונט (P3) בעמודת הערך ל-500% (פי 5) */
        .stDataFrame tbody tr td:nth-child(2) {
            font-size: 500%; 
            font-weight: bolder;
            white-space: normal; 
            line-height: 1.1; 
        }

        /* ודא שגבולות התאים ברורים */
        .stDataFrame table {
            border-collapse: collapse;
        }
        .stDataFrame th, .stDataFrame td {
            border: 1px solid #333; /* גבול ברור יותר */
        }
        
        /* ודא שהכותרות של העמודות מודגשות */
        .stDataFrame th {
            font-weight: bold !important;
        }
        
        </style>
        """, unsafe_allow_html=True)
    
    st.title("🔢 מפת הצ'אקרות ומחזורי החיים")
    st.markdown("---")
    
    # 1. קליטת קלט ממשתמש ב-Sidebar 
    with st.sidebar:
        st.header("הזנת נתונים")
        
        st.subheader("תאריך לידה")
        today = datetime.now()
        
        col_d, col_m, col_y = st.columns(3)
        # נתוני ברירת מחדל: 26/11/1976
        day = col_d.number_input("יום (DD):", min_value=1, max_value=31, value=26, key="d")
        month = col_m.number_input("חודש (MM):", min_value=1, max_value=12, value=11, key="m")
        year = col_y.number_input("שנה (YYYY):", min_value=1900, max_value=today.year, value=1976, key="y")
        
        st.subheader("שם מלא (בעברית)")
        # נתוני ברירת מחדל: תומר נוי
        first_name = st.text_input("שם פרטי:", "תומר")
        last_name = st.text_input("שם משפחה:", "נוי")
        
        st.markdown("---")
        
        calculate_button = st.button("לחץ לחישוב וניתוח התדרים", use_container_width=True)


    # 2. הצגת התוצאות
    if calculate_button or st.session_state.get('calculated', False):
        
        st.session_state['calculated'] = True
        
        try:
            # קריאה לפונקציה המעודכנת (מקבלים את analysis_text)
            df_cycles, df_chakras, analysis_text = run_numerology_tool_for_app(
                day, month, year, first_name, last_name
            )
            
            # ------------------------------------------------------
            # טבלה 1: מחזורי חיים (נשאר כטבלה רחבה)
            # ------------------------------------------------------
            st.header("1. מחזורי החיים (מתנה, משאל\"ה/שיא, אתגר)")
            
            cols_rtl_visual_order = [
                'מחזור חיים', 'תקופת חיים (גילאים)', 'מתנה (תדר+עוצמה)', 
                'משאל"ה/שיא (תדר+עוצמה)', 'אתגר (תדר+עוצמה)'
            ]
            
            cols_for_slice = cols_rtl_visual_order[::-1]
            
            # יצירת DataFrame לתצוגה שבו האתגר מוצג רק כמספר
            df_cycles_display = df_cycles.copy()
            # 🚨 תיקון: החלפת העמודה המלאה רק בערך המספרי הנקי
            df_cycles_display['אתגר (תדר+עוצמה)'] = df_cycles['__אתגר_נקי'].astype(str)
            
            df_cycles_filtered = df_cycles_display[cols_for_slice] 
            
            styled_df_cycles = df_cycles_filtered.style.apply(
                style_cycles_table, df_full_data=df_cycles, axis=None
            )
            
            st.dataframe(styled_df_cycles, use_container_width=True, hide_index=True)
            
            st.info("שימו לב: 'מתנה' ו'משאל\"ה/שיא' עשויים להכיל מספרי מאסטר וקארמה. 'אתגר' הוא תמיד חד-ספרתי.")
            
            st.markdown("---")

            # ------------------------------------------------------
            # 🚨 תצוגה 2: מפת הצ'אקרות (מפת ענק יציבה)
            # ------------------------------------------------------
            st.header("2. מפת תדרי הצ'אקרות")
            
            # 1. שינוי שמות העמודות לשמות קצרים וברורים
            df_chakras_display = df_chakras.rename(columns={
                'שם הצ\'אקרה': 'צ\'אקרה',
                'ערך נומרולוגי (ותדר)': 'ערך',
                'עוצמת התדר': 'אפיון'
            })
            
            # 2. סידור העמודות בסדר ש-Streamlit יציג כרצוי ב-RTL:
            # [אפיון (שמאל) | ערך (מרכז) | צ'אקרה (ימין)]
            final_cols = ['אפיון', 'ערך', 'צ\'אקרה']
            df_chakras_display = df_chakras_display[final_cols]
            
            # 3. צביעת טבלת הצ'אקרות
            styled_df_chakras = df_chakras_display.style.apply(
                highlight_chakras, axis=1
            )
            
            # 4. הצגת הטבלה במיכל מוגבל רוחב
            st.markdown('<div class="chakra-table-container">', unsafe_allow_html=True)
            st.dataframe(styled_df_chakras, hide_index=True, use_container_width=True) 
            st.markdown('</div>', unsafe_allow_html=True)
            
            # ------------------------------------------------------
            # 🚨 תצוגה 3: ניתוח השילובים
            # ------------------------------------------------------
            st.markdown("---")
            st.header("3. שילובים (ניתוח אישיות)")
            
            if analysis_text:
                # שימוש ב-Markdown לטקסט מעוצב
                st.markdown(analysis_text)
            else:
                st.info("לא נמצאו נתונים לניתוח שילובים.")
            
        except Exception as e:
            st.error(f"אירעה שגיאה בחישוב הנומרולוגי: {e}")

# ----------------------------------------------------
# הפעלת האפליקציה
# ----------------------------------------------------
if __name__ == '__main__':
    main()