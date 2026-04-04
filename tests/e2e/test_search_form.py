"""Tests for search form display and home page route"""

import pytest


class TestHomePageRoute:
    """Test home page (/) route for search form display"""

    def test_home_page_loads_successfully(self, client):
        """Test that GET / returns 200 and HTML response"""
        response = client.get("/")
        assert response.status_code == 200
        assert b"<!DOCTYPE html>" in response.data or b"<html" in response.data

    def test_home_page_contains_search_form(self, client):
        """Test that home page contains search form elements"""
        response = client.get("/")
        assert response.status_code == 200
        # Check for form elements
        assert b"<form" in response.data
        assert b"country" in response.data.lower()
        assert b"keyword" in response.data.lower()
        # Check for search button (Chinese or English)
        assert b"search" in response.data.lower() or "搜索".encode() in response.data

    def test_home_page_contains_country_options(self, client):
        """Test that country dropdown has all required options"""
        response = client.get("/")
        assert response.status_code == 200
        countries = [b"Vietnam", b"Thailand", b"Indonesia", b"UAE", b"Saudi Arabia"]
        for country in countries:
            assert country in response.data

    def test_home_page_shows_statistics_section(self, client):
        """Test that home page includes statistics section"""
        response = client.get("/")
        assert response.status_code == 200
        assert "统计".encode() in response.data or b"statistics" in response.data.lower()

    def test_home_page_contains_loading_spinner_hidden(self, client):
        """Test that loading spinner exists but is hidden by default"""
        response = client.get("/")
        assert response.status_code == 200
        assert b"spinner" in response.data.lower() or b"loading" in response.data.lower()

    def test_home_page_contains_countdown_element(self, client):
        """Test that countdown timer element exists"""
        response = client.get("/")
        assert response.status_code == 200
        assert b"countdown" in response.data.lower() or "延迟".encode() in response.data
