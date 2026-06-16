# Create New Module: $ARGUMENTS

Create module `backend/src/modules/$ARGUMENTS/` with these files in order:

1. `models.py`
   - SQLAlchemy 2.x async mapped classes
   - UUID primary key with uuid4 default
   - TimestampMixin (created_at, updated_at)
   - SoftDeleteMixin (is_deleted bool, default False)
   - Proper __tablename__
   - Index on every FK and filter column

2. `schemas.py`
   - Pydantic v2 models
   - Separate: `$ARGUMENTSCreate` (request), `$ARGUMENTSResponse` (response), `$ARGUMENTSDB` (internal)
   - No ORM objects in schemas

3. `repository.py`
   - Inherit `BaseRepository` from `core/base_repository.py`
   - Add domain-specific query methods
   - Type annotations on all methods
   - Return domain objects, never raw SQL rows

4. `service.py`
   - Import repository, call it — never import Session directly
   - Business logic only
   - Raise `HTTPException` from `core/exceptions.py`
   - Full type annotations

5. `router.py`
   - `APIRouter` with prefix and tags
   - `response_model=` on every endpoint
   - Auth via `Depends(get_current_user)` where needed
   - Rate limiting on mutation endpoints

After creation:
- Add Alembic migration: `uv run alembic revision --autogenerate -m "add_$ARGUMENTS"`
- Wire router into `backend/src/main.py`
- Update CLAUDE.md PROJECT STATUS
