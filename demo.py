import streamlit as st
import pandas as pd
import os
from io import BytesIO

def load_all_target_csv_and_preprocess_to_one_dataframe(data_dir):
    csv_files = [file for file in os.listdir(data_dir) if file.endswith('.csv')]
    result_df = pd.DataFrame()
    for file in csv_files:
        df = pd.read_csv(os.path.join(data_dir, file))
        df2 = df.iloc[2:].rename(columns=df.iloc[2])
        df3 = df2.drop(df2.index[:1]).reset_index(drop=True)
        df4 = df3.iloc[:-1]
        df4.loc[:, '营业日期'] = pd.to_datetime(df4['营业日期'])
        df4.loc[:, '下单时间'] = pd.to_datetime(df4['下单时间'])
        numeric_columns = ['食品销售均价', '下单数量', '取消数量', '销售数量', '净售数量', '下单金额', '取消金额', '销售金额', '优惠金额', '净售金额']
        df4.loc[:, numeric_columns] = df4[numeric_columns].apply(pd.to_numeric, errors='coerce')
        string_columns = list(set(df4.columns) - set(numeric_columns))
        df4[string_columns] = df4[string_columns].astype(str)
        result_df = pd.concat([result_df, df4], ignore_index=True)
    return result_df

def group_by_month_and_save_to_xlsx(df, output_file):
    df['下单时间'] = pd.to_datetime(df['下单时间'])
    grouped_df = df.groupby([df['食品大类'], df['食品名称'], df['下单时间'].dt.month])['净售金额'].sum().reset_index()
    grouped_df = grouped_df.sort_values(['下单时间', '食品大类'])
    pivot_df = pd.pivot_table(grouped_df, values='净售金额', index=['食品名称', '食品大类'], columns='下单时间', aggfunc='sum')
    pivot_df = pivot_df.fillna(0)
    for col in pivot_df.columns:
        if str(col).isdigit():
            pivot_df = pivot_df.rename(columns={col: str(col) + '月'})
    pivot_df['合计'] = pivot_df.apply(lambda row: sum(row), axis=1)
    special_foods = ['野菌瀑布灌汤包', '黑松露菌饺', '鸡枞卤肉糯米烧麦', '胡辣汤', '荷香糯米鸡', '普洱牛肉包', '奶白酒', '糖腿破酥包', '玫瑰鲜奶米布墨江紫米八宝粥', '普洱小炒鸡包子', '流汁黑猪肉包', '鲜肉烧麦', '鲜奶米布', '老面叉烧包', '奶黄流沙包', '玫瑰乌茶汤', '苏麻破酥包', '奶香叉烧包', '玫瑰豆沙包']
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        pivot_df.to_excel(writer, sheet_name='所有食品')
        special_df = pivot_df[pivot_df.index.get_level_values('食品名称').str.contains('|'.join(special_foods))]
        special_df.to_excel(writer, sheet_name='二楼食品')
        general_df = pivot_df[~pivot_df.index.get_level_values('食品名称').str.contains('|'.join(special_foods))]
        general_df.to_excel(writer, sheet_name='一楼食品')
    return output

st.title('数据分析应用')

uploaded_files = st.file_uploader("上传CSV文件", accept_multiple_files=True, type="csv")

if uploaded_files:
    st.write("已上传文件:")
    for uploaded_file in uploaded_files:
        st.write(uploaded_file.name)

    with st.spinner('正在处理...'):
        temp_dir = "temp_csvs"
        os.makedirs(temp_dir, exist_ok=True)
        for uploaded_file in uploaded_files:
            with open(os.path.join(temp_dir, uploaded_file.name), "wb") as f:
                f.write(uploaded_file.getbuffer())
        df = load_all_target_csv_and_preprocess_to_one_dataframe(temp_dir)
        output = group_by_month_and_save_to_xlsx(df, "output.xlsx")
        st.dataframe(df)
        st.success('处理完成!')
        st.download_button(label="下载处理后的文件", data=output.getvalue(), file_name="processed_data.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
