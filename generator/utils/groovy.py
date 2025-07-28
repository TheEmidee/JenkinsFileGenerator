def write_groovy_repr(context, val):
    if isinstance(val, bool):
        context.write("true" if val else "false")
    elif val is None:
        context.write("null")
    elif isinstance(val, str):
        context.write("'{}'".format(val.replace("'", "\\'")))
    else:
        context.write(str(val))

    return ""


def escape_quotes(text: str) -> str:
    """
    Escapes double quotes in the input string

    Args:
        text (str): The input string to escape.

    Returns:
        str: The escaped string with double quotes replaced.
    """
    return text.replace('"', '\\"')


def add_comments(text: str) -> str:
    """
    Takes a string as input and returns the same string with '//'
    added at the beginning of each line.

    Args:
        text (str): The input string

    Returns:
        str: The string with '//' prefix added to each line
    """
    lines = text.split("\n")
    commented_lines = ["//" + line for line in lines]
    return "\n".join(commented_lines)


def stubify(context, command: str, print_message: str):
    context.write(
        f"print( '{print_message}' )\n{add_comments(command)}"
        if command
        else "//" + print_message
    )

    return ""
