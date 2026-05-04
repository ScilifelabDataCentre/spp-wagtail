"""Tests for topic pages."""

from wagtail.models import Page, Site
from wagtail.test.utils import WagtailPageTestCase

from cms.pages import HomePage, TopicPage, TopicsIndexPage
from cms.tests.utils import create_test_image

#######################################################################
############# Helper classes and functions for testing ################
#######################################################################


class BasePageTestCase(WagtailPageTestCase):
    """Base test case for page tests, providing common setup and utilities."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Create a site setup with a home page and a topics index page for testing."""

        root = Page.get_first_root_node()
        for child in root.get_children():
            child.delete()
        root = Page.get_first_root_node()
        cls.home = HomePage(title="Home", slug="home")
        root.add_child(instance=cls.home)
        Site.objects.update_or_create(
            is_default_site=True,
            defaults={"hostname": "testserver", "root_page": cls.home},
        )

        cls.topics_index = TopicsIndexPage(title="Topics", slug="topics")
        cls.home.add_child(instance=cls.topics_index)
        cls.topics_index.save_revision().publish()


######################################################################
############### Test suite for TopicsIndexPage model #################
######################################################################


class TestTopicsIndexPage(BasePageTestCase):
    """Tests for the TopicsIndexPage model."""

    def test_max_count_set_on_model(self):
        """Test that only one instance of TopicsIndexPage can be created."""
        self.assertEqual(TopicsIndexPage.max_count, 1)

    def test_parent_page_type_restriction(self):
        """Test that only HomePage can be a parent of TopicsIndexPage."""
        self.assertEqual(TopicsIndexPage.parent_page_types, ["cms.HomePage"])

    def test_subpage_type_restriction(self):
        """Test that only TopicPage can be added as a child of TopicsIndexPage."""
        self.assertEqual(TopicsIndexPage.subpage_types, ["cms.TopicPage"])

    def test_get_context_includes_child_topics(self):
        """Test that the get_context method includes child TopicPage instances."""
        img2 = create_test_image(title="Image 2", file_name="image2.jpg")
        img1 = create_test_image(title="Image 1", file_name="image1.jpg")
        topic2 = TopicPage(title="Topic 2", slug="topic-2", description="Description 2", image=img2)
        topic1 = TopicPage(title="Topic 1", slug="topic-1", description="Description 1", image=img1)
        self.topics_index.add_child(instance=topic2)
        self.topics_index.add_child(instance=topic1)
        topic2.save_revision().publish()
        topic1.save_revision().publish()

        request = self.client.get(self.topics_index.url).wsgi_request
        context = self.topics_index.get_context(request)

        self.assertIn("topics", context)
        self.assertEqual(len(context["topics"]), 2)
        self.assertTrue(all(isinstance(t, TopicPage) for t in context["topics"]))
        self.assertEqual(context["topics"][0].title, "Topic 1")


######################################################################
################## Test suite for TopicPage model ####################
######################################################################


class TestTopicPage(BasePageTestCase):
    """Tests for the TopicPage model."""

    def test_parent_page_type_restriction(self):
        """Test that only TopicsIndexPage can be a parent of TopicPage."""
        self.assertEqual(TopicPage.parent_page_types, ["cms.TopicsIndexPage"])

    def test_subpage_type_restriction(self):
        """Test that TopicPage cannot have any child pages."""
        self.assertEqual(TopicPage.subpage_types, [])

    def test_image_field_is_required_by_model_constraint(self):
        """Test that the image field is required based on the model definition."""
        field = TopicPage._meta.get_field("image")
        self.assertFalse(field.blank)

    def test_description_is_required_by_model_constraint(self):
        """Test that the description field is required based on the model definition."""
        field = TopicPage._meta.get_field("description")
        self.assertFalse(field.blank)

    def test_topic_page_can_be_created_under_index(self):
        """Test that a TopicPage can be created under a TopicsIndexPage."""
        img = create_test_image(title="Test Image", file_name="test_image.jpg")
        topic_page = TopicPage(
            title="Test Topic",
            slug="test-topic",
            description="A test topic page.",
            image=img,
        )
        self.topics_index.add_child(instance=topic_page)
        topic_page.save_revision().publish()

        self.assertTrue(TopicPage.objects.filter(id=topic_page.id).exists())
        self.assertEqual(topic_page.get_parent().specific, self.topics_index)
