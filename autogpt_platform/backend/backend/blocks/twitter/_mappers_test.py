import pytest

from backend.blocks.twitter._mappers import (
    get_backend_expansion,
    get_backend_field,
    get_backend_list_expansion,
    get_backend_list_field,
    get_backend_media_field,
    get_backend_place_field,
    get_backend_poll_field,
    get_backend_reply_setting,
    get_backend_space_expansion,
    get_backend_space_field,
    get_backend_user_field,
)


# ── get_backend_expansion ────────────────────────────────────────────────────


def test_get_backend_expansion_valid():
    assert get_backend_expansion("Poll_IDs") == "attachments.poll_ids"


def test_get_backend_expansion_media_keys():
    assert get_backend_expansion("Media_Keys") == "attachments.media_keys"


def test_get_backend_expansion_author():
    assert get_backend_expansion("Author_User_ID") == "author_id"


def test_get_backend_expansion_invalid():
    with pytest.raises(KeyError, match="Invalid expansion key"):
        get_backend_expansion("NonExistent_Key")


# ── get_backend_reply_setting ────────────────────────────────────────────────


def test_get_backend_reply_setting_valid():
    assert get_backend_reply_setting("All_Users") == "all"


def test_get_backend_reply_setting_mentioned():
    assert get_backend_reply_setting("Mentioned_Users_Only") == "mentionedUsers"


def test_get_backend_reply_setting_following():
    assert get_backend_reply_setting("Following_Users_Only") == "following"


def test_get_backend_reply_setting_invalid():
    with pytest.raises(KeyError, match="Invalid reply setting key"):
        get_backend_reply_setting("Nobody")


# ── get_backend_user_field ───────────────────────────────────────────────────


def test_get_backend_user_field_valid():
    assert get_backend_user_field("Username") == "username"


def test_get_backend_user_field_display_name():
    assert get_backend_user_field("Display_Name") == "name"


def test_get_backend_user_field_id():
    assert get_backend_user_field("User_ID") == "id"


def test_get_backend_user_field_invalid():
    with pytest.raises(KeyError, match="Invalid user field key"):
        get_backend_user_field("Nonexistent_Field")


# ── get_backend_field (TweetFields) ──────────────────────────────────────────


def test_get_backend_field_valid():
    assert get_backend_field("Tweet_Text") == "text"


def test_get_backend_field_author_id():
    assert get_backend_field("Author_ID") == "author_id"


def test_get_backend_field_tweet_id():
    assert get_backend_field("Tweet_ID") == "id"


def test_get_backend_field_invalid():
    with pytest.raises(KeyError, match="Invalid field key"):
        get_backend_field("Unknown_Field")


# ── get_backend_poll_field ───────────────────────────────────────────────────


def test_get_backend_poll_field_valid():
    assert get_backend_poll_field("Poll_ID") == "id"


def test_get_backend_poll_field_duration():
    assert get_backend_poll_field("Duration_Minutes") == "duration_minutes"


def test_get_backend_poll_field_options():
    assert get_backend_poll_field("Poll_Options") == "options"


def test_get_backend_poll_field_invalid():
    with pytest.raises(KeyError, match="Invalid poll field key"):
        get_backend_poll_field("Bad_Key")


# ── get_backend_place_field ──────────────────────────────────────────────────


def test_get_backend_place_field_valid():
    assert get_backend_place_field("Country") == "country"


def test_get_backend_place_field_name():
    assert get_backend_place_field("Place_Name") == "name"


def test_get_backend_place_field_full_name():
    assert get_backend_place_field("Full_Location_Name") == "full_name"


def test_get_backend_place_field_invalid():
    with pytest.raises(KeyError, match="Invalid place field key"):
        get_backend_place_field("Invalid_Place")


# ── get_backend_media_field ──────────────────────────────────────────────────


def test_get_backend_media_field_valid():
    assert get_backend_media_field("Media_URL") == "url"


def test_get_backend_media_field_type():
    assert get_backend_media_field("Media_Type") == "type"


def test_get_backend_media_field_height():
    assert get_backend_media_field("Height") == "height"


def test_get_backend_media_field_invalid():
    with pytest.raises(KeyError, match="Invalid media field key"):
        get_backend_media_field("Fake_Field")


# ── get_backend_space_expansion ──────────────────────────────────────────────


def test_get_backend_space_expansion_valid():
    assert get_backend_space_expansion("Creator") == "creator_id"


def test_get_backend_space_expansion_hosts():
    assert get_backend_space_expansion("Hosts") == "host_ids"


def test_get_backend_space_expansion_speakers():
    assert get_backend_space_expansion("Speakers") == "speaker_ids"


def test_get_backend_space_expansion_invalid():
    with pytest.raises(KeyError, match="Invalid expansion key"):
        get_backend_space_expansion("Unknown_Expansion")


# ── get_backend_space_field ──────────────────────────────────────────────────


def test_get_backend_space_field_valid():
    assert get_backend_space_field("Space_Title") == "title"


def test_get_backend_space_field_id():
    assert get_backend_space_field("Space_ID") == "id"


def test_get_backend_space_field_state():
    assert get_backend_space_field("Space_State") == "state"


def test_get_backend_space_field_invalid():
    with pytest.raises(KeyError, match="Invalid space field key"):
        get_backend_space_field("Missing_Field")


# ── get_backend_list_expansion ───────────────────────────────────────────────


def test_get_backend_list_expansion_valid():
    assert get_backend_list_expansion("List_Owner_ID") == "owner_id"


def test_get_backend_list_expansion_invalid():
    with pytest.raises(KeyError, match="Invalid list expansion key"):
        get_backend_list_expansion("Nonexistent_Expansion")


# ── get_backend_list_field ───────────────────────────────────────────────────


def test_get_backend_list_field_valid():
    assert get_backend_list_field("List_Name") == "name"


def test_get_backend_list_field_id():
    assert get_backend_list_field("List_ID") == "id"


def test_get_backend_list_field_description():
    assert get_backend_list_field("Description") == "description"


def test_get_backend_list_field_invalid():
    with pytest.raises(KeyError, match="Invalid list field key"):
        get_backend_list_field("Unknown_List_Field")
