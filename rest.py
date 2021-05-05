import datetime
import sys
from flask import Flask
from flask_restful import Api, Resource, reqparse, inputs, fields, marshal_with, marshal
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)


@app.before_first_request
def create_tables():
    db.create_all()


api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///event.db'
db = SQLAlchemy(app)
parser = reqparse.RequestParser()
parser.add_argument('date', type=inputs.date,
                    help="The event date with the correct format is required! The correct format is YYYY-MM-DD!",
                    required=True)
parser.add_argument('event', type=str,
                    help="The event name is required!",
                    required=True)

resource_fields = {
    'id': fields.Integer,
    'event': fields.String,
    'date': fields.DateTime(dt_format='iso8601')
}


class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    event = db.Column(db.String(120), nullable=False)
    date = db.Column(db.Date, nullable=False)


@api.resource('/event/today')
class EventToday(Resource):
    @marshal_with(resource_fields)
    def get(self):
        events = Event.query.filter(Event.date == datetime.date.today()).all()
        return events


@api.resource('/event')
class AddEvent(Resource):
    @marshal_with(resource_fields)
    def get(self):
        parser_date = reqparse.RequestParser()
        parser_date.add_argument('start_time', type=inputs.date,
                                 help="The event date with the correct format is required! The correct format is YYYY-MM-DD!",
                                 required=False)
        parser_date.add_argument('end_time', type=inputs.date,
                                 help="The event date with the correct format is required! The correct format is YYYY-MM-DD!",
                                 required=False)

        args = parser_date.parse_args()
        start = args.get('start_time', None)
        end = args.get('end_time', None)
        if start is None or end is None:
            events = Event.query.all()
        else:
            events = Event.query.filter(Event.date.between(start, end)).all()
        return events

    @staticmethod
    def post():
        args = parser.parse_args()
        event = Event(event=args["event"], date=args["date"])
        db.session.add(event)
        db.session.commit()
        msg = {"message": "The event has been added!",
               "event": args["event"],
               "date": args["date"].strftime("%Y-%m-%d")}
        return msg, 200


@api.resource('/event/<int:event_id>')
class EventByID(Resource):

    @staticmethod
    def get(event_id):
        event = Event.query.get(event_id)
        if event:
            return marshal(event, resource_fields)
        return {"message": "The event doesn't exist!"}, 404

    @staticmethod
    def delete(event_id):
        event = Event.query.get(event_id)
        if event:
            db.session.delete(event)
            db.session.commit()
            return {"message": "The event has been deleted!"}
        return {"message": "The event doesn't exist!"}, 404


if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        app.run(host=arg_host, port=arg_port)
    else:
        app.run()
