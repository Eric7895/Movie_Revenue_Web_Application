from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Float, Date, CheckConstraint

Base = declarative_base()

class Movies(Base):
    __tablename__ = 'Movie'

    primaryTitle = Column(String(200), primary_key=True, nullable=False)
    titleType = Column(
        String(50),
        nullable=False,
        comment='Allowed values: "movie", "tvSeries"',
    )
    genres = Column(String(50), nullable=False, comment='A string with comma as separator')
    directors = Column(String(600), nullable=False, comment='A string with comma as separator')
    writers = Column(String(500), nullable=False, comment='A string with comma as separator')
    averageRating = Column(
        Float,
        nullable=False,
        comment='Average IMDb rating for this movie (0 to 10)',
    )
    numVotes = Column(Float, nullable=False, comment='Number of IMDb votes for this movie')
    actors = Column(String(5000), nullable=True, comment='A string with comma as separator')
    original_language = Column(
        String(50),
        nullable=False,
        comment="Language abbreviation (e.g., 'en', 'ja', 'zh', etc.)",
    )
    production_companies = Column(String(1000), nullable=False, comment='A string with comma as separator')
    release_date = Column(Date, primary_key=True, nullable=False)
    budget = Column(Float, nullable=False)
    revenue = Column(Float, nullable=True)
    runtime = Column(Float, nullable=False)
    status = Column(String(50), nullable=False)
    keywords = Column(String(1000), nullable=True, comment='A string with "-" as separator')
    trailer_views = Column(Float, nullable=True)
    trailer_likes = Column(Float, nullable=True)

    # Adding a CheckConstraint separately for titleType
    __table_args__ = (
        CheckConstraint(titleType.in_(['movie', 'tvMovie']), name="check_titleType"),
        CheckConstraint(status.in_(['Released', 'Not Released']), name="check_status"),
    )
