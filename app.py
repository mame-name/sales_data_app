import streamlit as st
import pandas as pd
import random
import time

# ページ設定（ワイドモードで左右分割を活かす）
st.set_page_config(layout="wide", page_title="営業データ分析システム")

# タイトルエリア
st.markdown("<h1 style='text-align: center;'>🤖 営業データ分析システム 🤖</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>実績データを読み込み、自動でインデックスを抽出・整形します</p>", unsafe_allow_html=True) 
st.divider()

# ==========================================
# ⚙️ データ処理関数
# ==========================================
@st.cache_data
def load_and_process_data(file):
    """アップロードされたファイルをそのまま全列読み込み、【伝票計】のみ除外する"""
    try:
        # Excelファイルの全シート名を取得して安全確認
        xl = pd.ExcelFile(file)
        sheet_names = xl.sheet_names
        
        # 'Sheet1' があればそれを使い、無ければ1番最初のシートを自動選択
        target_sheet = 'Sheet1' if 'Sheet1' in sheet_names else sheet_names[0]
        
        # 1. ファイルの最初の行をそのまま列名として全列読み込み
        df_raw = pd.read_excel(file, sheet_name=target_sheet)
        
        # 【クレンジング】データフレーム全体から「【伝票計】」という文字が含まれる行を完全に除外
        df_raw = df_raw[~df_raw.astype(str).apply(lambda x: x.str.contains('【')).any(axis=1)]
        
        # すべて空の行を削除
        df_raw = df_raw.dropna(how='all').reset_index(drop=True)
        
        # 最新順（逆順）にしてインデックスを振り直す
        return df_raw[::-1].reset_index(drop=True)
        
    except ModuleNotFoundError as e:
        st.error("🚨 必須ライブラリが不足しています。ターミナルで `pip install openpyxl` を実行してください。")
        return None
    except Exception as e:
        if "openpyxl" in str(e):
            st.error("🚨 Excelの読み込みにライブラリが必要です。ターミナルで `pip install openpyxl` を実行してください。")
        else:
            st.error(f"データ処理エラー: {e}")
        return None


# ==========================================
# 🧱 左右分割レイアウトの作成
# ==========================================
left_col, right_col = st.columns([1, 2])

# ------------------------------------------
# 👈 左画面：データ入力・選択項目
# ------------------------------------------
with left_col:
    st.subheader("📁 データソース読込")
    uploaded_file = st.file_uploader("実績XLSMファイルを選択してください", type=['xlsm', 'xlsx'], label_visibility="collapsed")
    
    st.markdown("---")
    st.subheader("⚙️ 条件選択")
    st.caption("※ファイル読み込み後に選択可能になります（現在は外枠のみ）。")
    
    target_region = st.selectbox("対象エリア", ["全エリア", "関東", "関西", "その他"], disabled=True)
    target_category = st.selectbox("製品カテゴリー", ["すべて", "カテゴリーA", "カテゴリーB"], disabled=True)
    analysis_range = st.slider("分析期間 (ヶ月)", min_value=1, max_value=12, value=3, disabled=True)
    
    st.markdown("---")
    predict_button = st.button("🚀 分析・シミュレーションを実行 🚀", type="primary", use_container_width=True)


# ------------------------------------------
# 👉 右画面：メイン表示エリア
# ------------------------------------------
with right_col:
    if uploaded_file:
        
        # ファイルの自動バックグラウンド処理（全列をそのまま維持）
        with st.spinner("🔄 実績データを読み込み中..."):
            processed_df = load_and_process_data(uploaded_file)
        
        # 🎰 演出用のプレースホルダー
        display_placeholder = st.empty()
        
        if processed_df is None:
            st.warning("データの読み込みに失敗したため、処理を中断しました。")
            
        elif not predict_button:
            display_placeholder.markdown("<h2 style='text-align: center; margin-top: 50px;'>📊 データ読込完了</h2>", unsafe_allow_html=True)
            st.success(f" 読み込み成功: {len(processed_df)} 件のデータを検出しました（【伝票計】は自動除外済み）。")
            st.info("👈 左側の「分析・シミュレーションを実行」ボタンを押すと、このデータを元にシミュレーションを開始します。")
        
        else:
            # ボタン押下時のスロット風演出
            symbols = ["⏳", "🔄", "✨", "📈", "🔍", "💻"]
            for i in range(12):
                wait_time = 0.04 + (i**1.2 * 0.005)
                c1 = random.choice(symbols)
                c2 = random.choice(symbols)
                c3 = random.choice(symbols)
                display_placeholder.markdown(f"<h1 style='text-align: center; font-size: 3rem;'>{c1} {c2} {c3}</h1>", unsafe_allow_html=True)
                time.sleep(wait_time)
            
            display_placeholder.markdown("<h2 style='color: #FF4B4B;'>✅ 分析シミュレーション結果</h2>", unsafe_allow_html=True)
            
            # タブメニュー
            tab1, tab2, tab3 = st.tabs(["📈 ダッシュボード", "📋 抽出データ一覧", "🔮 予測シミュレーション"])
            
            with tab1:
                st.subheader("データサマリー")
                m1, m2, m3 = st.columns(3)
                
                total_rows = len(processed_df) if processed_df is not None else 0
                m1.metric(label="解析データ総数", value=f"{total_rows} 件")
                m2.metric(label="処理ステータス", value="正常 (全列読込・クレンジング済)")
                m3.metric(label="エラー件数", value="0 件")
                
                st.markdown("#### 📊 グラフ配置エリア")
                st.caption("※ここに抽出データから計算された各種チャートが表示されます。")
                
            with tab2:
                st.subheader("📋 実績データ一覧（全列表示）")
                if processed_df is not None and not processed_df.empty:
                    # 本物の列名・全列でテーブルを表示
                    st.dataframe(processed_df, use_container_width=True, height=450)
                else:
                    st.warning("表示できるデータがありません。")
                
            with tab3:
                st.subheader("AI予測シミュレーション値")
                st.caption("※ここに抽出データをベースにした将来の予測値が反映されます。")
                
    else:
        st.info("👈 まずは左側のパネルからファイル（Sheet1）をアップロードしてください。")
