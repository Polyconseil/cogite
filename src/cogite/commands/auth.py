from cogite import auth
from cogite import interaction


def choose_token_getter(getters):
    """Ask the user to choose a token getter amongst those available."""
    if len(getters) == 1:
        _label, getter = getters[0]
        return getter
    interaction.display("cogite needs a personal access token. There are several ways to get one:")
    for idx, (label, _) in enumerate(getters, start=1):
        interaction.display(f"{idx}. {label}")
    choices = range(1, len(getters) + 1)
    while 1:
        choices_help = ', '.join(str(i) for i in range(1, len(getters)))
        choices_help += f' or {len(getters)}'
        choice = input(
            f"Please choose one of the methods above by typing {choices_help}, followed by Enter: "
        )
        try:
            choice = int(choice)
        except ValueError:
            pass
        else:
            if choice in choices:
                _label, getter = getters[choice - 1]
                return getter
        interaction.display("[[error]] Wrong choice. Try again.")


def add_auth(context):
    configuration = context.configuration

    if auth.get_token(context.host_domain):
        interaction.display("You already have an authentication token for the current Git host.")
        interaction.display(
            "If you want to create a new token, you must first delete the existing "
            "token with `cogite auth delete`."
        )
        return

    getters = auth.get_token_getters(configuration)
    getter = choose_token_getter(getters)
    token = getter().get_token()
    auth.save_token(context.host_domain, token)
    interaction.display("[[success]] This token has been saved. You're ready to go!")


def delete_auth(context):
    if not auth.get_token(context.host_domain):
        interaction.display(
            f"[[error]] No authentication token exists for the current "
            f"Git host: {context.host_domain}"
        )
        return
    interaction.display(
        f"[[warning]] [[caution]]You are about to delete the authentication token "
        f"linked to {context.host_domain}[[/]]",
    )
    if not interaction.confirm(defaults_to_yes=False):
        interaction.display("All right, no authentication token has been deleted.")
        return
    auth.delete_token(context.host_domain)
    interaction.display("[[success]] The authentication token has been deleted.")
