from database import (
    add_document,
    get_documents,
    delete_document,
    update_document,
    get_document_stats,
    get_profile,
    save_profile,
)


class TestDocumentCRUD:
    def test_add_document(self):
        add_document(
            "Passport",
            "Passport",
            "2024-01-01",
            "2034-01-01",
            30,
            "My passport",
            "08:00",
        )
        docs = get_documents()
        assert len(docs) == 1
        assert docs[0]["name"] == "Passport"
        assert docs[0]["category"] == "Passport"
        assert docs[0]["expiry_date"] == "2034-01-01"

    def test_add_document_no_expiry(self):
        add_document(
            "Birth Certificate",
            "Certificate",
            "2000-01-01",
            "",
            7,
            "No expiry doc",
            "08:00",
        )
        docs = get_documents()
        assert len(docs) == 1
        assert docs[0]["expiry_date"] == ""

    def test_get_documents_search(self):
        add_document(
            "Passport",
            "Passport",
            "2024-01-01",
            "2034-01-01",
            30,
            "Indian passport",
            "08:00",
        )
        add_document(
            "License", "License", "2024-01-01", "2030-01-01", 7, "Driving", "09:00"
        )

        results = get_documents("Passport")
        assert len(results) == 1
        assert results[0]["name"] == "Passport"

        results = get_documents("Driving")
        assert len(results) == 1
        assert results[0]["name"] == "License"

    def test_delete_document(self):
        add_document(
            "Test Doc", "Other", "2024-01-01", "2025-01-01", 7, "notes", "08:00"
        )
        docs = get_documents()
        assert len(docs) == 1

        delete_document(docs[0]["id"])
        docs = get_documents()
        assert len(docs) == 0

    def test_update_document(self):
        add_document(
            "Old Name", "Other", "2024-01-01", "2025-01-01", 7, "old notes", "08:00"
        )
        docs = get_documents()
        doc_id = docs[0]["id"]

        update_document(
            doc_id,
            "New Name",
            "License",
            "2024-06-01",
            "2030-06-01",
            30,
            "new notes",
            "10:00",
        )

        docs = get_documents()
        assert docs[0]["name"] == "New Name"
        assert docs[0]["category"] == "License"
        assert docs[0]["expiry_date"] == "2030-06-01"
        assert docs[0]["reminder_days"] == 30
        assert docs[0]["alert_time"] == "10:00"
        assert docs[0]["notes"] == "new notes"


class TestDocumentStats:
    def test_stats_empty(self):
        stats = get_document_stats()
        assert stats["total"] == 0
        assert stats["active"] == 0
        assert stats["expired"] == 0
        assert stats["expiring_soon"] == 0

    def test_stats_with_documents(self):
        # Expired
        add_document("Expired", "Other", "2020-01-01", "2020-06-01", 7, "x", "08:00")
        # Active (far future)
        add_document("Active", "Other", "2024-01-01", "2030-01-01", 7, "x", "08:00")

        stats = get_document_stats()
        assert stats["total"] == 2
        assert stats["expired"] == 1
        assert stats["active"] == 1


class TestProfile:
    def test_default_profile(self):
        profile = get_profile()
        assert profile["full_name"] == ""
        assert profile["emails"] == ""
        assert profile["phones"] == ""

    def test_save_and_get_profile(self):
        save_profile(
            full_name="John Doe",
            emails="john@example.com, john2@example.com",
            phones="Austria: +43 123\nIndia: +91 456",
            passport_number="AB1234567",
            driving_license="DL-9876",
            address="Austria: Vienna\nIndia: Bangalore",
            date_of_birth="1990-05-15",
            nationality="Indian",
        )

        profile = get_profile()
        assert profile["full_name"] == "John Doe"
        assert "john@example.com" in profile["emails"]
        assert "Austria: +43 123" in profile["phones"]
        assert profile["passport_number"] == "AB1234567"
        assert profile["driving_license"] == "DL-9876"
        assert "Vienna" in profile["address"]
        assert profile["date_of_birth"] == "1990-05-15"
        assert profile["nationality"] == "Indian"

    def test_profile_update_overwrites(self):
        save_profile("First", "", "", "", "", "", "", "")
        save_profile("Second", "a@b.com", "", "", "", "", "", "")

        profile = get_profile()
        assert profile["full_name"] == "Second"
        assert profile["emails"] == "a@b.com"
