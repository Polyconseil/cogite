from cogite import auth
from cogite import interaction


def choose_token_getter(getters):
    """Ask the user to choose a token getter amongst those available."""
    if len(getters) == 1:
        _label, getter = getters[0]
        return getter
    print("cogite needs a personal access token. There are several ways to get one:")
    for idx, (label, _) in enumerate(getters, start=1):
        print(f"{idx}. {label}")
    choices = range(1, len(getters) + 1)
    while 1:
        choices_help = ', '.join(str(i) for i in range(1, len(getters)))
        choices_help += f' or {len(getters)}'
        choice = input(
            f"Please choose one of the methods above by typing {choices_help}: "
        )
        try:
            choice = int(choice)
        except ValueError:
            pass
        else:
            if choice in choices:
                _label, getter = getters[choice - 1]
                return getter
        print("Wrong choice. Try again.")


def add_auth(context):
    configuration = context.configuration

    if auth.get_token(context.host_domain):
        print("You already have an authentication token for the current Git host.")
        print(
            "If you want to create a new token, you must first delete the existing "
            "token with `cogite auth delete`."
        )
        return

    getters = auth.get_token_getters(configuration)
    getter = choose_token_getter(getters)
    token = getter().get_token()
    auth.save_token(context.host_domain, token)
    print("This token has been saved. You're ready to go!")


def delete_auth(context):
    if not auth.get_token(context.host_domain):
        print(
            f"No authentication token exists for the current "
            f"Git host: {context.host_domain}"
        )
        return
    print(
        f"You are about to delete the authentication token "
        f"linked to {context.host_domain}",
    )
    if not interaction.confirm(defaults_to_yes=False):
        print("All right, no authentication token has been deleted.")
        return
    auth.delete_token(context.host_domain)
    print("The authentication token has been deleted.")
