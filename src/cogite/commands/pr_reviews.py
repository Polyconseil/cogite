from cogite import completion
from cogite import interaction
from cogite import spinner


def request_reviews(context):
    client = context.client
    with spinner.get_for_git_host_call():
        collaborators = client.get_collaborators()
    users = completion.prompt_for_users(collaborators)
    if users:
        with spinner.get_for_git_host_call():
            client.request_reviews(users)
        interaction.display("[[success]] Reviews have been requested.")
