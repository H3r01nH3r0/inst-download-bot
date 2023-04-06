from sqlalchemy.ext.declarative import declarative_base
import sqlalchemy as sa

Base = declarative_base()


class Users(Base):
    __tablename__ = "users"

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, unique=True, nullable=False)
    username = sa.Column(sa.String)
    tariff = sa.Column(sa.Integer, sa.ForeignKey("tariffs.id"), default=None)
    balance = sa.Column(sa.Integer, nullable=False, default=0)


class Tariffs(Base):
    __tablename__ = "tariffs"

    id = sa.Column(sa.Integer, primary_key=True)
    tariff_price = sa.Column(sa.Integer, nullable=False)
    tariff_days = sa.Column(sa.Integer, nullable=False)


class Subscribers(Base):
    __tablename__ = "subscribers"

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.user_id"))
    start_time = sa.Column(sa.DateTime, nullable=False)
    end_time = sa.Column(sa.DateTime, nullable=False)


class UsersRequests(Base):
    __tablename__ = "user_request"

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.user_id"))
    request_name = sa.Column(sa.Text, nullable=False)
    request_link = sa.Column(sa.Text, nullable=False)

class Payments(Base):
    __tablename__ = "payments"

    id = sa.Column(sa.Integer, primary_key=True)
    payment_id = sa.Column(sa.Text, nullable=False)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.user_id"))
    user_email = sa.Column(sa.Text, nullable=False)
    payment_description = sa.Column(sa.Text, nullable=False)
    payment_url = sa.Column(sa.Text, nullable=False)


class SavedPayments(Base):
    __tablename__ = "saved_payments"

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.user_id"))
    email = sa.Column(sa.Text, nullable=False)
    card = sa.Column(sa.Text, nullable=False)
    method_id = sa.Column(sa.Text, nullable=False)


class UserMedia(Base):
    __tablename__ = "user_media"

    id = sa.Column(sa.Integer, primary_key=True)
    username = sa.Column(sa.Text, nullable=False)
    user_id = sa.Column(sa.Text, nullable=False)
    media_pk = sa.Column(sa.Integer, nullable=False)
    media_type = sa.Column(sa.Integer, nullable=False)
    url = sa.Column(sa.Text, default=None)
    caption = sa.Column(sa.Text, nullable=True, default="No Caption")


class Carousel(Base):
    __tablename__ = "carousel"

    id = sa.Column(sa.Integer, primary_key=True)
    media_id = sa.Column(sa.Integer, sa.ForeignKey("user_media.id"), nullable=False)
    media_type = sa.Column(sa.Integer, nullable=False)
    url = sa.Column(sa.Text, nullable=False)


class WatchUpdates(Base):
    __tablename__ = "watch_updates"

    id = sa.Column(sa.Integer, primary_key=True)
    user_id = sa.Column(sa.Integer, sa.ForeignKey("users.user_id"))
    target_username = sa.Column(sa.Text, nullable=False)
    target_id = sa.Column(sa.Text, nullable=False)
    last_watch = sa.Column(sa.DateTime, nullable=False)


class Discount(Base):
    __tablename__ = "discount"

    id = sa.Column(sa.Integer, primary_key=True)
    discount_value = sa.Column(sa.Integer, nullable=False)
    discount_id = sa.Column(sa.Integer, nullable=False)
    expire_date = sa.Column(sa.DateTime, nullable=False)


class AdminRefs(Base):
    __tablename__ = "admin_refs"

    id = sa.Column(sa.Integer, primary_key=True)
    channel_name = sa.Column(sa.Text, nullable=False)
    link = sa.Column(sa.Text, nullable=False)
    count = sa.Column(sa.Integer, default=0)
