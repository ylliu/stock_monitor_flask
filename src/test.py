import datetime
import os
import sys
import threading
import time
from datetime import datetime
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

from src.local_csv_interface import LocalCsvInterface
from src.tushare_interface import TushareInterface
from src.washing_strategy import WashingStrategyConfig, WashingStrategy

WIN = sys.platform.startswith('win')
if WIN:  # 如果是 Windows 系统，使用三个斜线
    prefix = 'sqlite:///'
else:  # 否则使用四个斜线
    prefix = 'sqlite:////'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = prefix + os.path.join(app.root_path, '../data.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控
# 在扩展类实例化前加载配置
db = SQLAlchemy(app)
CORS(app)  # 添加这一行来启用 CORS 支持


class StockConfig(db.Model):
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


class StockMonitorRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    time = db.Column(db.String(50))
    stock_code = db.Column(db.String(10))
    description = db.Column(db.String(200))
    below_5_day_line = db.Column(db.Boolean, default=False)
    below_10_day_line = db.Column(db.Boolean, default=False)
    concept = db.Column(db.String(200))


@app.route('/config', methods=['GET', 'POST'])
def stock_config():
    if request.method == 'GET':
        config = StockConfig.query.order_by(StockConfig.id.desc()).first()
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
            })
        else:
            return jsonify({'error': 'No configuration found'}), 404
    elif request.method == 'POST':
        data = request.get_json()
        print("post:", data)
        config = StockConfig(
            first_day_vol_ratio=data['first_day_vol_ratio'],
            free_float_value_range_min=data['free_float_value_range_min'],
            free_float_value_range_max=data['free_float_value_range_max'],
            circulation_value_range_min=data['circulation_value_range_min'],
            circulation_value_range_max=data['circulation_value_range_max'],
            second_candle_new_high_days=data['second_candle_new_high_days'],
            ma10_ratio=data['ma10_ratio'],
            days_to_ma10=data['days_to_ma10'],
            ma5_trigger=data['ma5_trigger'],
            ma10_trigger=data['ma10_trigger']
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


@app.route('/monitor_records/<date>', methods=['GET'])
def get_monitor_records(date):
    back_days = 10
    end_date = '2024-10-28'
    local_running = 1
    volume_rate = 1.5
    positive_average_pct = 10
    second_positive_high_days = 15
    before_positive_circ_mv = 30
    positive_to_ten_mean_periods = 10
    ten_mean_scaling_factor = 1.001
    strategy_config = WashingStrategyConfig(back_days, end_date, local_running, volume_rate, positive_average_pct,
                                            second_positive_high_days, before_positive_circ_mv,
                                            positive_to_ten_mean_periods, ten_mean_scaling_factor)
    data_interface = TushareInterface()
    stock_list = data_interface.get_all_stocks('创业板')
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
            if csv_date == pre_trade_data:
                data_interface.update_local_csv_data_fast(stock_list)
            data_interface.update_csv_data(stock_list, 300)

    data_interface = LocalCsvInterface()
    data_interface.load_csv_data(stock_list)
    washing_strategy = WashingStrategy(stock_list, end_date, back_days, 1, data_interface, strategy_config)
    washing_strategy.update_realtime_data(end_date)
    search_results = washing_strategy.find()
    print(search_results)
    # records = StockMonitorRecord.query.all()
    # print(records)
    if search_results:
        return jsonify([{
            'id': 'id',
            'time': record.end_date,
            'stock_code': record.code,
            'description': record.name,
            'below_5_day_line': True,
            'below_10_day_line': True,
            'concept': record.concept
        } for record in search_results]), 200
    else:
        return jsonify({'error': 'No records found for this date'}), 404


with app.app_context():
    # db.drop_all()  # This will delete everything
    print('11111')
    db.create_all()
    print('22222')
    get_monitor_records('2024-10-23')


def create_tables():
    with app.app_context():
        db.drop_all()
        db.create_all()


if __name__ == '__main__':
    with app.app_context():
        print("ddd:")

    create_tables()
    app.run(debug=True)
