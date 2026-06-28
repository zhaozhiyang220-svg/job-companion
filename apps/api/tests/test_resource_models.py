from sqlalchemy.orm import Session

from src.models import (
    ResourceCollection,
    ResourceCollectionLink,
    ResourceItem,
    ResourceType,
    User,
)


def test_create_resource_and_collection(db: Session) -> None:
    u = User(preferences={})
    db.add(u)
    db.flush()
    coll = ResourceCollection(user_id=u.id, name="字节面试")
    res = ResourceItem(
        user_id=u.id,
        type=ResourceType.INTERVIEW_RECALL,
        title="豆包 PM 二面面经",
        content_text="...",
    )
    db.add_all([coll, res])
    db.flush()
    db.add(ResourceCollectionLink(collection_id=coll.id, resource_id=res.id))
    db.flush()
    assert res.type == ResourceType.INTERVIEW_RECALL
    assert coll.name == "字节面试"
