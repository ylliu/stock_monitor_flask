import datetime
import sys
import threading
import time

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

WIN = sys.platform.startswith('win')
if WIN:  # 如果是 Windows 系统，使用三个斜线
    prefix = 'sqlite:///'
else:  # 否则使用四个斜线
    prefix = 'sqlite:////'

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stock_config.db'
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
    min_positive_days = db.Column(db.Integer, nullable=False)


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
                'min_positive_days': config.min_positive_days
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
            min_positive_days=data['min_positive_days']
        )
        db.session.add(config)
        db.session.commit()
        return jsonify(data), 201


def monitor_stock():
    with app.app_context():
        while True:
            stock_code = "300001.SZ"
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


with app.app_context():
    db.drop_all()  # This will delete everything
    print('11111')
    db.create_all()
    print('22222')


def create_tables():
    with app.app_context():
        db.create_all()


if __name__ == '__main__':
    with app.app_context():
        print("ddd:")

    create_tables()
    app.run(debug=True)
