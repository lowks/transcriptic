def natural_sort(l):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(l, key=alphanum_key)

def pull(nested_dict):
    if "type" in nested_dict and "inputs" not in nested_dict:
        return nested_dict
    else:
        inputs = {}
        if "type" in nested_dict and "inputs" in nested_dict:
            for param, input in nested_dict["inputs"].items():
                inputs[str(param)] = pull(input)
            return inputs
        else:
            return nested_dict

def regex_manifest(protocol, input):
    '''Special input types, gets updated as more input types are added'''
    if "type" in input and input["type"] == "choice":
        if "options" in input:
            pattern = '\[(.*?)\]'
            match = re.search(pattern, str(input["options"]))
            if not match:
                click.echo("Error in %s: input type \"choice\" options must be in the "
                           "form of: \n[\n  {\n  \"value\": <choice value>, \n  \"label\": "
                           "<choice label>\n  },\n  ...\n]" % protocol['name'])
                raise RuntimeError
        else:
            click.echo("Must have options for 'choice' input type." +
                               " Error in: " + protocol["name"])
            raise RuntimeError

def iter_json(manifest):
    all_types = {}
    try:
        protocol = manifest['protocols']
    except TypeError:
        raise RuntimeError("Error: Your manifest.json file doesn't contain valid JSON and"
                           " cannot be formatted.")
    for protocol in manifest["protocols"]:
        types = {}
        for param, input in protocol["inputs"].items():
            types[param] = pull(input)
            if isinstance(input, dict):
                if input["type"] == "group" or input["type"] == "group+":
                    for i, j in input.items():
                        if isinstance(j, dict):
                            for k, l in j.items():
                                regex_manifest(protocol, l)
                else:
                    regex_manifest(protocol, input)
        all_types[protocol["name"]] = types
    return all_types

def robotize(well_ref, well_count, col_count):
    """Function referenced from autoprotocol.container_type.robotize()"""
    if not isinstance(well_ref, (basestring, int)):
        raise TypeError("ContainerType.robotize(): Well reference given "
                        "is not of type 'str' or 'int'.")

    well_ref = str(well_ref)
    m = re.match("([a-z])(\d+)$", well_ref, re.I)
    if m:
        row = ord(m.group(1).upper()) - ord('A')
        col = int(m.group(2)) - 1
        well_num = row * col_count + col
        # Check bounds
        if row > (well_count/col_count):
            raise ValueError("Row given exceeds "
                             "container dimensions.")
        if col > col_count or col < 0:
            raise ValueError("Col given exceeds "
                             "container dimensions.")
        if well_num > well_count:
            raise ValueError("Well given "
                             "exceeds container dimensions.")
        return well_num
    else:
        m = re.match("\d+$", well_ref)
        if m:
            well_num = int(m.group(0))
            # Check bounds
            if well_num > well_count or well_num < 0:
                raise ValueError("Well number "
                                 "given exceeds container dimensions.")
            return well_num
        else:
            raise ValueError("Well must be in "
                             "'A1' format or be an integer.")

def humanize(well_ref, well_count, col_count):
    """Function referenced from autoprotocol.container_type.humanize()"""
    if not isinstance(well_ref, int):
        raise TypeError("Well reference given "
                        "is not of type 'int'.")
    idx = robotize(well_ref, well_count, col_count)
    row, col = (idx // col_count, idx % col_count)
    # Check bounds
    if well_ref > well_count or well_ref < 0:
            raise ValueError("Well reference "
                             "given exceeds container dimensions.")
    return "ABCDEFGHIJKLMNOPQRSTUVWXYZ"[row] + str(col + 1)

def by_well(datasets, well):
    return [datasets[reading].props['data'][well][0] for reading in datasets.keys()]
