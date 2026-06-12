from sqlalchemy import select

from app.models import (Embedding, EventLog, Listing, Product, ProductStatus,
                        ProductType, Trend)


async def test_create_product(db):
    p = Product(title="Test", product_type=ProductType.pdf_planner)
    db.add(p)
    await db.commit()
    assert p.id is not None
    assert p.status == ProductStatus.draft


async def test_product_listing_relationship_is_one_to_many(db):
    p = Product(title="Test", product_type=ProductType.pdf_planner)
    p.listings = [Listing(title="L1"), Listing(title="L2")]
    db.add(p)
    await db.commit()
    rows = await db.execute(select(Listing).where(Listing.product_id == p.id))
    assert len(rows.scalars().all()) == 2  # uselist=False would have broken this


async def test_embedding_vector_roundtrip_on_sqlite(db):
    e = Embedding(ref_type="product", ref_id=1, vector=[0.1, 0.2, 0.3])
    db.add(e)
    await db.commit()
    row = (await db.execute(select(Embedding))).scalar_one()
    assert row.vector == [0.1, 0.2, 0.3]


async def test_all_eleven_tables_exist():
    from app.core.database import Base
    assert len(Base.metadata.tables) == 11


async def test_event_log(db):
    db.add(EventLog(level="INFO", source="test", message="hello"))
    await db.commit()
    assert (await db.execute(select(EventLog))).scalar_one().message == "hello"


async def test_trend(db):
    db.add(Trend(keyword="budget planner", niche="finance", score=0.8))
    await db.commit()
    assert (await db.execute(select(Trend))).scalar_one().score == 0.8
