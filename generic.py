import collections

# Generic functions that I will eventually librarize.
# ------------------------------------------------------------


def _tree_merge (trees): 
    def update(d, u):
        for k, v in u.iteritems():
            if isinstance(v, collections.Mapping):
                r = update(d.get(k, {}), v)
                d[k] = r
            else:
                d[k] = u[k]
        return d
    return reduce (update, trees)

def _device_mapper_path_escape (path):
    return ''.join ( [ char + char if char == '-' else char for char in list (path) ] )

# Vital global constants.
# -----------------------

conf_path = '/etc/machineer/machineer.conf'

# Operations common for all schemata.
# -----------------------------------

dev = {}

