def write_groovy_repr(context,val):
    if isinstance(val, bool):
        context.write('true' if val else 'false')
    elif val is None:
        context.write('null')
    elif isinstance(val, str):
        context.write("'{}'".format(val.replace("'", "\\'")))
    else:
        context.write(str(val))

    return ''