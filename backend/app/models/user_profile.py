from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, PickleType
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(String, primary_key=True)  # user_id
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    interest_vector = Column(PickleType, nullable=False)  # np.ndarray TF-IDF 500-dim
    semantic_vector = Column(PickleType, nullable=True)   # 384-dim sentence-transformer vector
    als_vector = Column(PickleType, nullable=True)        # 32-dim ALS latent factors (User×Channel)
    top_categories = Column(PickleType, nullable=True)    # List[str]
    top_topics = Column(PickleType, nullable=True)        # List[str]
    video_count = Column(String, nullable=False, default="0")  # stored as string for compatibility
    computed_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="profile")
