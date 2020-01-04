from datetime import datetime, timedelta
import unittest
from app import app, db
from app.models import User, Post


class UserModelCase(unittest.TestCase):
    def setUp(self):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_password_hashing(self):
        u = User(username='susan')
        u.set_password('cat')
        self.assertFalse(u.check_password('dog'))
        self.assertTrue(u.check_password('cat'))

    def test_avatar(self):
        u = User(username='john', email='john@example.com')
        self.assertEqual(u.avatar(128), ('http://www.gravatar.com/avatar/'
                                         'd4c74594d841139328695756648b6bd6'
                                         '?d=identicon&s=128'))

    def test_follow(self):
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        self.assertEqual(u1.followed.all(), [])
        self.assertEqual(u1.followers.all(), [])

        u1.follow(u2)
        db.session.commit()
        self.assertTrue(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 1)
        self.assertEqual(u1.followed.first().username, 'susan')
        self.assertEqual(u2.followers.count(), 1)
        self.assertEqual(u2.followers.first().username, 'john')

        u1.unfollow(u2)
        db.session.commit()
        self.assertFalse(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 0)
        self.assertEqual(u2.followers.count(), 0)

    def test_follow_posts(self):
        # create four users
        create_users = lambda name:User(username=name, email=name + '@example.com')
        usernames = ['john', 'susan', 'mary', 'david']
        users = []
        for username in usernames:
            users.append(create_users(username))
        db.session.add_all(users)

        #create four posts
        now = datetime.utcnow()
        create_posts = lambda user, delta:Post(body="post from " + user.username,
                                               author=user,
                                               timestamp=now + timedelta(
                                                   seconds=delta))
        posts = []
        deltas = [1, 4, 3, 2]
        for i, user in enumerate(users):
            posts.append(create_posts(user, deltas[i]))
        db.session.add_all(posts)
        db.session.commit()

        #setup the followers
        users[0].follow(users[1]) # john follows susan
        users[0].follow(users[3]) # john follows david
        users[1].follow(users[2]) # susan follows mary
        users[2].follow(users[3]) # mary follows david
        db.session.commit()

        # test entry
        present_posts = []
        for user in users:
            present_posts.append(user.followed_posts().all())
        self.assertEqual(present_posts[0], [posts[1], posts[3], posts[0]])
        self.assertEqual(present_posts[1], [posts[1], posts[2]])
        self.assertEqual(present_posts[2], [posts[2], posts[3]])
        self.assertEqual(present_posts[3], [posts[3]])


if __name__ == '__main__':
    unittest.main(verbosity=2)
