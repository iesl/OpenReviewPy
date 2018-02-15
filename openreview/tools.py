#!/usr/bin/python
import openreview
import re

super_user_id = 'OpenReview.net'

def get_profile(client, value):
    profile = None
    try:
        profile = client.get_profile(value)
    except openreview.OpenReviewException as e:
        # throw an error if it is something other than "not found"
        if e[0][0] != 'Profile not found':
            print "OpenReviewException: {0}".format(e)
            return e
    return profile

def create_profile(client, email, first, last, middle = None):

    profile = get_profile(client, email)

    if not profile:
        response = client.get_tildeusername(first, last, middle)
        tilde_id = response['username'].encode('utf-8')

        if tilde_id.endswith(last + '1'):

            tilde_group = openreview.Group(id = tilde_id, signatures = [super_user_id], signatories = [tilde_id], readers = [tilde_id], writers = [super_user_id], members = [email])
            email_group = openreview.Group(id = email, signatures = [super_user_id], signatories = [email], readers = [email], writers = [super_user_id], members = [tilde_id])
            profile_content = {
                'emails': [email],
                'preferred_email': email,
                'names': [
                    {
                        'first': first,
                        'middle': middle,
                        'last': last,
                        'username': tilde_id
                    }
                ]
            }
            client.post_group(tilde_group)
            client.post_group(email_group)
            profile = client.post_profile(tilde_id, profile_content)

            return profile

        else:
            raise openreview.OpenReviewException('There is already a profile with this first: {0}, middle: {1}, last name: {2}'.format(first, middle, last))
    else:
        raise openreview.OpenReviewException('There is already a profile with this email: {0}'.format(email))


def build_groups(conference_group_id, default_params=None):
    '''

    Given a group ID, returns a list of empty groups that correspond to the given group's subpaths
    (e.g. Test.com, Test.com/TestConference, Test.com/TestConference/2018)

    '''

    path_components = conference_group_id.split('/')
    paths = ['/'.join(path_components[0:index+1]) for index, path in enumerate(path_components)]

    if not default_params:
        default_params = {
            'readers': ['everyone'],
            'writers': [],
            'signatures': [],
            'signatories': [],
            'members': []
        }

    groups = {p: openreview.Group(p, **default_params) for p in paths}
    groups[conference_group_id].writers = groups[conference_group_id].signatories = [conference_group_id]

    return sorted(groups.values(), key=lambda x: len(x.id))

def get_bibtex(note, venue_fullname, year, url_forum=None, accepted=False, anonymous=True):

    def capitalize_title(title):
        capitalization_regex = re.compile('[A-Z]{2,}')
        words = re.split('(\W)', title)
        for idx, word in enumerate(words):
            m = capitalization_regex.search(word)
            if m:
                new_word = '{' + word[m.start():m.end()] + '}'
                words[idx] = words[idx].replace(word[m.start():m.end()], new_word)
        return ''.join(words)


    first_word = re.sub('[^a-zA-Z]', '', note.content['title'].split(' ')[0].lower())

    forum = note.forum if not url_forum else url_forum

    if anonymous:
        first_author_last_name = 'anonymous'
        authors = 'Anonymous'
    else:
        first_author_last_name = note.content['authors'][0].split(' ')[1].lower()
        authors = ' and '.join(note.content['authors'])

    bibtex_title = capitalize_title(note.content['title'])

    rejected_bibtex = [
        '@misc{',
        first_author_last_name + year + first_word + ',',
        'title={' + bibtex_title + '},',
        'author={' + authors + '},',
        'year={' + year + '},',
        'url={https://openreview.net/forum?id=' + forum + '},',
        '}'
    ]

    accepted_bibtex = [
        '@inproceedings{',
        first_author_last_name + '2018' + first_word + ',',
        'title={' + bibtex_title + '},',
        'author={' + authors + '},',
        'booktitle={' + venue_fullname + '},',
        'year={' + year + '},',
        'url={https://openreview.net/forum?id=' + forum + '},',
        '}'
    ]

    if accepted:
        bibtex = accepted_bibtex
    else:
        bibtex = rejected_bibtex

    return '\n'.join(bibtex)

