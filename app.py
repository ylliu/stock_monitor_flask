from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 添加这一行来启用 CORS 支持
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///stock_config.db'
db = SQLAlchemy(app)


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
                'days_to_ma10': config.days_to_ma10
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
            days_to_ma10=data['days_to_ma10']
        )
        db.session.add(config)
        db.session.commit()
        return jsonify(data), 201


with app.app_context():
    print('11111')
    db.create_all()
    print('22222')

if __name__ == '__main__':
    print("ddd:")

    dd = app.app_context()
    print("ddd:", dd)
    with app.app_context():
        print('11111')
        db.create_all()
        print('22222')
    app.run(debug=True)
