import datetime
import os
import sys
import threading
import time
from datetime import datetime

import pandas as pd
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

from src.local_csv_interface import LocalCsvInterface
from src.shared_data import search_results_data
from src.tushare_interface import TushareInterface
from src.washing_strategy import WashingStrategyConfig, WashingStrategy, SearchResult, RealInfo

WIN = sys.platform.startswith('win')
if WIN:  # 如果是 Windows 系统，使用三个斜线
    prefix = 'sqlite:///'
else:  # 否则使用四个斜线
    prefix = 'sqlite:////'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(app.root_path, './data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控
# 在扩展类实例化前加载配置
db = SQLAlchemy(app)
CORS(app)  # 添加这一行来启用 CORS 支持
CORS(app, resources={r"/*": {"origins": "*"}})
search_results = []
is_updating = False
main = "main"
chi_next = "chiNext"


class StockChinextConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_day_vol_ratio = db.Column(db.Float, nullable=False)
    free_float_value_range_min = db.Column(db.Float, nullable=False)
    free_float_value_range_max = db.Column(db.Float, nullable=False)
    circulation_value_range_min = db.Column(db.Float, nullable=False)
    circulation_value_range_max = db.Column(db.Float, nullable=False)
    second_candle_new_high_days = db.Column(db.Integer, nullable=False)
    ma10_ratio = db.Column(db.Float, nullable=False)
    days_to_ma10 = db.Column(db.Integer, nullable=False)
    ma5_trigger = db.Column(db.Boolean, nullable=False)
    ma10_trigger = db.Column(db.Boolean, nullable=False)
    two_positive_pct_avg = db.Column(db.Integer, nullable=False)
    min_positive_days = db.Column(db.Integer, nullable=False)


class StockMainConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_day_vol_ratio = db.Column(db.Float, nullable=False)
    free_float_value_range_min = db.Column(db.Float, nullable=False)
    free_float_value_range_max = db.Column(db.Float, nullable=False)
    circulation_value_range_min = db.Column(db.Float, nullable=False)
    circulation_value_range_max = db.Column(db.Float, nullable=False)
    second_candle_new_high_days = db.Column(db.Integer, nullable=False)
    ma10_ratio = db.Column(db.Float, nullable=False)
    days_to_ma10 = db.Column(db.Integer, nullable=False)
    ma5_trigger = db.Column(db.Boolean, nullable=False)
    ma10_trigger = db.Column(db.Boolean, nullable=False)
    two_positive_pct_avg = db.Column(db.Float, nullable=False)
    min_positive_days = db.Column(db.Integer, nullable=False)


class StockMonitorRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.String(50))
    stock_code = db.Column(db.String(10))
    description = db.Column(db.String(200))
    below_5_day_line = db.Column(db.Boolean, default=False)
    below_10_day_line = db.Column(db.Boolean, default=False)
    concept = db.Column(db.String(200))


@app.route('/config/<board>', methods=['GET', 'POST'])
def stock_config(board):
    if request.method == 'GET':
        if board == main:
            config = StockMainConfig.query.order_by(StockMainConfig.id.desc()).first()
            print(config)
        elif board == chi_next:
            config = StockChinextConfig.query.order_by(StockChinextConfig.id.desc()).first()
            print(config)
        if config:
            return jsonify({
                'first_day_vol_ratio': config.first_day_vol_ratio,
                'free_float_value_range_min': config.free_float_value_range_min,
                'free_float_value_range_max': config.free_float_value_range_max,
                'circulation_value_range_min': config.circulation_value_range_min,
                'circulation_value_range_max': config.circulation_value_range_max,
                'second_candle_new_high_days': config.second_candle_new_high_days,
                'ma10_ratio': config.ma10_ratio,
                'days_to_ma10': config.days_to_ma10,
                'ma5_trigger': config.ma5_trigger,
                'ma10_trigger': config.ma10_trigger,
                'two_positive_pct_avg': config.two_positive_pct_avg,
                'min_positive_days': config.min_positive_days
            })
        else:
            return jsonify({'error': 'No configuration found'}), 404
    elif request.method == 'POST':
        data = request.get_json()
        print("post:", data)
        if board == main:
            config = StockMainConfig(
                first_day_vol_ratio=data['first_day_vol_ratio'],
                free_float_value_range_min=data['free_float_value_range_min'],
                free_float_value_range_max=data['free_float_value_range_max'],
                circulation_value_range_min=data['circulation_value_range_min'],
                circulation_value_range_max=data['circulation_value_range_max'],
                second_candle_new_high_days=data['second_candle_new_high_days'],
                ma10_ratio=data['ma10_ratio'],
                days_to_ma10=data['days_to_ma10'],
                ma5_trigger=data['ma5_trigger'],
                ma10_trigger=data['ma10_trigger'],
                two_positive_pct_avg=data['two_positive_pct_avg'],
                min_positive_days=data['min_positive_days']
            )
        elif board == chi_next:
            config = StockChinextConfig(
                first_day_vol_ratio=data['first_day_vol_ratio'],
                free_float_value_range_min=data['free_float_value_range_min'],
                free_float_value_range_max=data['free_float_value_range_max'],
                circulation_value_range_min=data['circulation_value_range_min'],
                circulation_value_range_max=data['circulation_value_range_max'],
                second_candle_new_high_days=data['second_candle_new_high_days'],
                ma10_ratio=data['ma10_ratio'],
                days_to_ma10=data['days_to_ma10'],
                ma5_trigger=data['ma5_trigger'],
                ma10_trigger=data['ma10_trigger'],
                two_positive_pct_avg=data['two_positive_pct_avg'],
                min_positive_days=data['min_positive_days']
            )

        db.session.add(config)
        db.session.commit()
        return jsonify(data), 201


def monitor_stock():
    with app.app_context():
        while True:
            stock_code = "300004.SZ"
            current_price = 30.1
            five_day_avg = 29.5
            log_event(stock_code, True, False, '创业板')
            time.sleep(60)  # 每分钟检查一次


def log_event(stock_code, below_5_day_line, below_10_day_line, concept):
    with app.app_context():
        if below_10_day_line is True:
            description = "低于10日线"
        elif below_5_day_line is True:
            description = f"低于5日线"
        event = StockMonitorRecord(
            time=str(datetime.datetime.now()),
            stock_code=stock_code,
            description=description,
            concept=concept,
            below_5_day_line=below_5_day_line,
            below_10_day_line=below_10_day_line
        )
        db.session.add(event)
        db.session.commit()


@app.route('/start_monitor', methods=['GET'])
def start_monitor():
    thread = threading.Thread(target=monitor_stock)
    thread.start()
    return jsonify({"message": f"Started monitoring"}), 200


@app.route('/monitor_records/<date>/<board>', methods=['GET'])
def get_monitor_records(date, board):
    if is_updating:
        return jsonify({'error': 'Is updating data please wait'}), 201
    print(date)
    if board == main:
        config = StockMainConfig.query.order_by(StockMainConfig.id.desc()).first()
        board_name = "主板"
    elif board == chi_next:
        config = StockChinextConfig.query.order_by(StockChinextConfig.id.desc()).first()
        board_name = "创业板"
    back_days = config.days_to_ma10 + 5
    end_date = date
    local_running = 1
    volume_rate = config.first_day_vol_ratio
    positive_average_pct = config.two_positive_pct_avg
    second_positive_high_days = config.second_candle_new_high_days
    before_positive_limit_circ_mv_min = config.free_float_value_range_min
    before_positive_limit_circ_mv_max = config.free_float_value_range_max
    before_positive_free_circ_mv_min = config.circulation_value_range_min
    before_positive_free_circ_mv_max = config.circulation_value_range_max
    positive_to_ten_mean_periods = config.days_to_ma10
    ten_mean_scaling_factor = config.ma10_ratio
    min_positive_days = config.min_positive_days
    strategy_config = WashingStrategyConfig(back_days, end_date, local_running, volume_rate, positive_average_pct,
                                            second_positive_high_days, before_positive_limit_circ_mv_min,
                                            before_positive_limit_circ_mv_max, before_positive_free_circ_mv_min,
                                            before_positive_free_circ_mv_max,
                                            positive_to_ten_mean_periods, ten_mean_scaling_factor, min_positive_days)
    data_interface = TushareInterface()
    stock_list = data_interface.get_all_stocks(board_name)
    # stock_list = ['601226.SH']
    last_code = stock_list[-1]
    first_code = stock_list[0]
    if local_running == 1:
        # data_interface.update_local_csv_data_fast(stock_list)
        if not data_interface.is_data_updated(last_code) or not data_interface.is_data_updated(first_code):
            csv_date = data_interface.find_last_date_in_csv(f'src/data/{last_code}_daily_data.csv')  # 0710
            now = datetime.now()
            # 获取当前小时数（24小时制）
            current_hour = now.hour
            pre_trade_data = data_interface.find_pre_data_publish_date(data_interface.get_today_date(), current_hour)
            # if csv_date == pre_trade_data:
            #     data_interface.update_local_csv_data_fast(stock_list)
            data_interface.update_csv_data(stock_list, 300)

    local_data_interface = LocalCsvInterface()
    local_data_interface.load_csv_data(stock_list)
    washing_strategy = WashingStrategy(stock_list, end_date, back_days, 1, local_data_interface, strategy_config)
    washing_strategy.update_realtime_data(end_date)
    # result = SearchResult('300001.sz', 'name', 10, '2024-10-28',
    #                       '2024-10-29', '2024-10-28', '2024-10-28',
    #                       30, 'concept')
    # search_results = []
    # search_results.append(result)
    search_results = washing_strategy.find()
    washing_strategy.save_to_xlsx(search_results, end_date)

    search_results_data.clear()
    search_results_data.extend(search_results)
    print(search_results)
    # records = StockMonitorRecord.query.all()
    # print(records)
    if search_results:
        return jsonify([{
            'id': 'id',
            'time': record.end_date,
            'stock_code': record.code,
            'stock_name': record.name,
            'below_5_day_line': False,
            'below_10_day_line': False,
            'limit_circ_mv': record.limit_circ_mv,
            'free_circ_mv': record.free_circ_mv,
            'bullish_start_date': record.start_date,
            'bullish_end_date': record.end_date,
            'concept': record.concept,
            'max_turnover_rate': record.max_turnover_rate,
            'angle_of_5': record.angle_of_5,
            'angle_of_10': record.angle_of_10,
            'angle_of_20': record.angle_of_20,
            'angle_of_30': record.angle_of_30,
        } for record in search_results]), 200
    else:
        return jsonify({'error': 'No records found for this date'}), 404


@app.route('/verity_code/<date>/<board>/<code>', methods=['GET'])
def verity_code(date, board, code):
    if is_updating:
        return jsonify({'error': 'Is updating data please wait'}), 201
    print(date)
    if board == main:
        config = StockMainConfig.query.order_by(StockMainConfig.id.desc()).first()
        board_name = "主板"
    elif board == chi_next:
        config = StockChinextConfig.query.order_by(StockChinextConfig.id.desc()).first()
        board_name = "创业板"
    back_days = config.days_to_ma10 + 5
    end_date = date
    local_running = 1
    volume_rate = config.first_day_vol_ratio
    positive_average_pct = config.two_positive_pct_avg
    second_positive_high_days = config.second_candle_new_high_days
    before_positive_limit_circ_mv_min = config.free_float_value_range_min
    before_positive_limit_circ_mv_max = config.free_float_value_range_max
    before_positive_free_circ_mv_min = config.circulation_value_range_min
    before_positive_free_circ_mv_max = config.circulation_value_range_max
    positive_to_ten_mean_periods = config.days_to_ma10
    ten_mean_scaling_factor = config.ma10_ratio
    min_positive_days = config.min_positive_days
    strategy_config = WashingStrategyConfig(back_days, end_date, local_running, volume_rate, positive_average_pct,
                                            second_positive_high_days, before_positive_limit_circ_mv_min,
                                            before_positive_limit_circ_mv_max, before_positive_free_circ_mv_min,
                                            before_positive_free_circ_mv_max,
                                            positive_to_ten_mean_periods, ten_mean_scaling_factor, min_positive_days)
    data_interface = TushareInterface()
    stock_list = [code]
    # stock_list = ['300044.SZ']
    last_code = stock_list[-1]
    first_code = stock_list[0]
    if local_running == 1:
        # data_interface.update_local_csv_data_fast(stock_list)
        if not data_interface.is_data_updated(last_code) or not data_interface.is_data_updated(first_code):
            csv_date = data_interface.find_last_date_in_csv(f'src/data/{last_code}_daily_data.csv')  # 0710
            now = datetime.now()
            # 获取当前小时数（24小时制）
            current_hour = now.hour
            pre_trade_data = data_interface.find_pre_data_publish_date(data_interface.get_today_date(), current_hour)
            # if csv_date == pre_trade_data:
            #     data_interface.update_local_csv_data_fast(stock_list)
            data_interface.update_csv_data(stock_list, 300)

    local_data_interface = LocalCsvInterface()
    local_data_interface.load_csv_data(stock_list)
    washing_strategy = WashingStrategy(stock_list, end_date, back_days, 1, local_data_interface, strategy_config)
    washing_strategy.update_realtime_data(end_date)
    # result = SearchResult('300001.sz', 'name', 10, '2024-10-28',
    #                       '2024-10-29', '2024-10-28', '2024-10-28',
    #                       30, 'concept')
    # search_results = []
    # search_results.append(result)
    search_results = washing_strategy.find()
    washing_strategy.save_to_xlsx(search_results, end_date)

    search_results_data.clear()
    search_results_data.extend(search_results)
    print(search_results)
    # records = StockMonitorRecord.query.all()
    # print(records)
    if search_results:
        return jsonify([{
            'id': 'id',
            'time': record.end_date,
            'stock_code': record.code,
            'stock_name': record.name,
            'below_5_day_line': False,
            'below_10_day_line': False,
            'limit_circ_mv': record.limit_circ_mv,
            'free_circ_mv': record.free_circ_mv,
            'bullish_start_date': record.start_date,
            'bullish_end_date': record.end_date,
            'concept': record.concept
        } for record in search_results]), 200
    else:
        return jsonify({'error': 'No records found for this date'}), 404


#
# @app.route('/monitor_records/zb/<date>', methods=['GET'])
# def get_monitor_records(date):
#     if is_updating:
#         return jsonify({'error': 'Is updating data please wait'}), 201
#     print(date)
#     config = StockZBConfig.query.order_by(StockZBConfig.id.desc()).first()
#     back_days = 15
#     end_date = date
#     local_running = 1
#     volume_rate = config.first_day_vol_ratio
#     positive_average_pct = 11
#     second_positive_high_days = config.second_candle_new_high_days
#     before_positive_limit_circ_mv_min = config.free_float_value_range_min
#     before_positive_limit_circ_mv_max = config.free_float_value_range_max
#     before_positive_free_circ_mv_min = config.circulation_value_range_min
#     before_positive_free_circ_mv_max = config.circulation_value_range_max
#     positive_to_ten_mean_periods = config.days_to_ma10
#     ten_mean_scaling_factor = config.ma10_ratio
#     strategy_config = WashingStrategyConfig(back_days, end_date, local_running, volume_rate, positive_average_pct,
#                                             second_positive_high_days, before_positive_limit_circ_mv_min,
#                                             before_positive_limit_circ_mv_max, before_positive_free_circ_mv_min,
#                                             before_positive_free_circ_mv_max,
#                                             positive_to_ten_mean_periods, ten_mean_scaling_factor)
#     data_interface = TushareInterface()
#     stock_list = data_interface.get_all_stocks('主板')
#     # stock_list = ['300044.SZ']
#     last_code = stock_list[-1]
#     first_code = stock_list[0]
#     if local_running == 1:
#         # data_interface.update_local_csv_data_fast(stock_list)
#         if not data_interface.is_data_updated(last_code) or not data_interface.is_data_updated(first_code):
#             csv_date = data_interface.find_last_date_in_csv(f'src/data/{last_code}_daily_data.csv')  # 0710
#             now = datetime.now()
#             # 获取当前小时数（24小时制）
#             current_hour = now.hour
#             pre_trade_data = data_interface.find_pre_data_publish_date(data_interface.get_today_date(), current_hour)
#             # if csv_date == pre_trade_data:
#             #     data_interface.update_local_csv_data_fast(stock_list)
#             data_interface.update_csv_data(stock_list, 300)
#
#     local_data_interface = LocalCsvInterface()
#     local_data_interface.load_csv_data(stock_list)
#     washing_strategy = WashingStrategy(stock_list, end_date, back_days, 1, local_data_interface, strategy_config)
#     washing_strategy.update_realtime_data(end_date)
#     # result = SearchResult('300001.sz', 'name', 10, '2024-10-28',
#     #                       '2024-10-29', '2024-10-28', '2024-10-28',
#     #                       30, 'concept')
#     # search_results = []
#     # search_results.append(result)
#     search_results = washing_strategy.find()
#     washing_strategy.save_to_xlsx(search_results, end_date)
#
#     search_results_data.clear()
#     search_results_data.extend(search_results)
#     print(search_results)
#     # records = StockMonitorRecord.query.all()
#     # print(records)
#     if search_results:
#         return jsonify([{
#             'id': 'id',
#             'time': record.end_date,
#             'stock_code': record.code,
#             'stock_name': record.name,
#             'below_5_day_line': False,
#             'below_10_day_line': False,
#             'limit_circ_mv': record.limit_circ_mv,
#             'free_circ_mv': record.free_circ_mv,
#             'bullish_start_date': record.start_date,
#             'bullish_end_date': record.end_date,
#             'concept': record.concept
#         } for record in search_results]), 200
#     else:
#         return jsonify({'error': 'No records found for this date'}), 404


@app.route('/stock_K_info/<stock_code>', methods=['GET'])
def get_stock_k_line(stock_code):
    local_data_interface = LocalCsvInterface()
    end_date = local_data_interface.find_nearest_trading_day(local_data_interface.get_today_date())
    k_lines = local_data_interface.get_daily_lines_from_csv(stock_code, end_date, 50)
    if k_lines:
        return jsonify([{
            'close': line.close,
            'high': line.high,
            'low': line.low,
            'open': line.open,
            'timestamp': datetime.strptime(line.trade_date, "%Y-%m-%d %H:%M:%S").timestamp() * 1000,
            'volume': line.vol
        } for line in k_lines]), 200
    else:
        return jsonify({'error': 'No line found for this date'}), 404


@app.route('/stock_price', methods=['GET'])
def get_stock_price():
    print()
    result = []
    code_list = []
    # 这里可以编写获取股票价格的代码，stock_code 是传递进来的股票代码参数
    if len(search_results_data) == 0:
        return jsonify({'error': 'Please click select stock'}), 404
    data_interface = TushareInterface()
    for search in search_results_data:
        code_list.append(search.code)

        # Splitting codes into chunks of 50 for batch processing
    chunked_codes = [code_list[i:i + 40] for i in range(0, len(code_list), 40)]
    dfs = []
    for chunk in chunked_codes:
        code_string = concat_code(chunk)
        df = data_interface.get_realtime_info(code_string)
        dfs.append(df)
        print(dfs)
        # Combine data frames

    # print(code_string)
    df = pd.concat(dfs, ignore_index=True)
    # df = data_interface.get_realtime_info(code_string)
    # print(df)

    for search in search_results_data:
        stock_price = df.loc[df['TS_CODE'] == search.code, 'PRICE'].values[0]
        pre_close_price = df.loc[df['TS_CODE'] == search.code, 'PRE_CLOSE'].values[0]
        stock_change = round((stock_price - pre_close_price) / pre_close_price * 100, 2)
        stock_low = df.loc[df['TS_CODE'] == search.code, 'LOW'].values[0]
        limit_circ_mv = search.limit_circ_mv
        free_circ_mv = search.free_circ_mv
        five_days_mean = data_interface.get_five_days_mean(stock_price, search.code)
        ten_days_mean = data_interface.get_ten_days_mean(stock_price, search.code)
        max_turnover_rate = search.max_turnover_rate
        angle_of_5 = search.angle_of_5
        angle_of_10 = search.angle_of_10
        angle_of_20 = search.angle_of_20
        angle_of_30 = search.angle_of_30
        if five_days_mean is None or ten_days_mean is None:
            continue
        if stock_low < five_days_mean:
            is_low_ma5 = True
        else:
            is_low_ma5 = False
        if stock_low < ten_days_mean:
            is_low_ma10 = True
        else:
            is_low_ma10 = False
        result.append(
            RealInfo(search.code, search.name, stock_price, stock_change, limit_circ_mv, free_circ_mv, is_low_ma5,
                     is_low_ma10, search.start_date, search.end_date,
                     search.concept, max_turnover_rate, angle_of_5, angle_of_10, angle_of_20, angle_of_30))

    if result:
        return jsonify([{
            'id': 'id',
            'stock_code': record.code,
            'stock_name': record.name,
            'stock_price': record.price,
            'stock_change': record.change,
            'limit_circ_mv': record.limit_circ_mv,
            'free_circ_mv': record.free_circ_mv,
            'below_5_day_line': record.is_low_ma5,
            'below_10_day_line': record.is_low_ma10,
            'bullish_start_date': record.start_date,
            'bullish_end_date': record.end_date,
            'concept': record.concept,
            'max_turnover_rate': record.max_turnover_rate,
            'angle_of_5': record.angle_of_5,
            'angle_of_10': record.angle_of_10,
            'angle_of_20': record.angle_of_20,
            'angle_of_30': record.angle_of_30,

        } for record in result]), 200
    else:
        return jsonify({'error': 'No records found for this date'}), 404
    # return jsonify({"stock_code": stock_code,
    #                 "stock_price": stock_price,
    #                 "stock_change": stock_change}), 200
    # return jsonify({
    #         'id': 'id',
    #         'time': '2024-10-28',
    #         'stock_code': '30001.sz',
    #         'stock_name': '半分',
    #         'below_5_day_line': True,
    #         'below_10_day_line': True,
    #         'concept': '概念'
    #     }),200
    result = SearchResult('300001.sz', 'name', 10, '2024-10-28',
                          '2024-10-29', '2024-10-28', '2024-10-28',
                          30, 'concept')
    search_results = []
    search_results.append(result)
    if search_results:
        return jsonify([{
            'id': 'id',
            'time': record.end_date,
            'stock_code': record.code,
            'stock_name': record.name,
            'below_5_day_line': True,
            'below_10_day_line': True,
            'concept': record.concept
        } for record in search_results]), 200
    else:
        return jsonify({'error': 'No records found for this date'}), 404


def concat_code(code_list):
    code_string = ','.join(code_list)
    return code_string


def update_data():
    data_interface = TushareInterface()
    stock_list = data_interface.get_all_stocks('主板,创业板')
    # stock_list = ['300044.SZ']
    last_code = stock_list[-1]
    first_code = stock_list[0]
    if True:
        if not data_interface.is_data_updated(last_code) or not data_interface.is_data_updated(first_code):
            csv_date = data_interface.find_last_date_in_csv(f'src/data/{last_code}_daily_data.csv')  # 0710
            now = datetime.now()
            # 获取当前小时数（24小时制）
            current_hour = now.hour
            pre_trade_data = data_interface.find_pre_data_publish_date(data_interface.get_today_date(), current_hour)
            # if csv_date == pre_trade_data:
            #     data_interface.update_local_csv_data_fast(stock_list)
            data_interface.update_csv_data(stock_list, 300)

    local_data_interface = LocalCsvInterface()
    local_data_interface.load_csv_data(stock_list)


#
# with app.app_context():
#     db.drop_all()  # This will delete everything
#     print('11111')
#     db.create_all()
#     print('22222')
#     # get_monitor_records('2024-10-23')


# def create_tables():
#     with app.app_context():
#         db.drop_all()
#         db.create_all()
#         # get_monit


def scheduled_task():
    # 每天定时执行任务
    while True:
        current_time = datetime.now()
        print(current_time)
        if current_time.weekday() <= 5 and current_time.hour == 19 and current_time.minute == 0:
            # 在周一到周五的晚上7点执行任务
            print("执行任务...")
            global is_updating
            is_updating = True
            update_data()
            is_updating = False
            # 在这里添加你的任务代码
        time.sleep(30)


thread = threading.Thread(target=scheduled_task)
thread.start()

if __name__ == '__main__':
    print("ddd:")

    # create_tables()
    app.run(host='0.0.0.0', port=5000)
