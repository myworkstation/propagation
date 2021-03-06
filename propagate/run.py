import os.path

import numpy as np

import data
import command_line

def parse_commandline(args):
    parser = command_line.create_parser()

    parser.add_argument('--validation', dest="validation", type=str, default=None, help="A validation dataset, that is use 'prior' +'network' to predict 'validation'")
    return parser.parse_args(args)

def validate(result, validation):
    import sklearn.metrics as metrics
    fpr, tpr, _ = metrics.roc_curve(validation>0, result)
    return tpr, fpr, metrics.auc(fpr, tpr)

if __name__ == '__main__':
    import sys
    
    opts = parse_commandline(sys.argv[1:])
    succeeded = command_line.is_valid_args(opts)

    if opts.validation is not None and not os.path.exists(opts.validation):
        succeeded = False
        print "Invalid validation filename"
    
    if succeeded:
        network = data.read_ppi(opts.network)
        if opts.prior is not None:
            prior = data.read_prior(opts.prior, network.names)
            if np.any(np.abs(prior) > 1.0):
                sys.stderr.write("Scaling prior, values outside [-1,1]\n")
                prior /= np.max(np.abs(prior), axis=0)
        else:
            prior = np.ones((network.graph.shape[0],1))

        if opts.validation is not None:
            validation = data.read_prior(opts.validation, network.names)
          
        result = network.normalize().smooth(prior,
                                            alpha=opts.alpha,
                                            eps=opts.epsilon,
                                            max_iter=opts.iterations)

        if opts.validation is not None:
            tpr, fpr, auc = validate(result, validation)
            print "fpr: ", fpr
            print "tpr: ", tpr
            print "auc: ", auc
        elif opts.clusters:
            import analysis
            clusters = analysis.find_connected_ilp(network, result)

            for c in clusters:
                print ','.join(str(x) for x in c)
        else:
            o = np.argsort(result[:,0])
            result = result[o,:]
            names = network.names.index[o]
            for n, r in zip(names, result):
                print "\t".join((n, np.str.join("\t", r.astype(str))))
