import java.io.*;
import java.io.File;
import java.net.URL;
import java.util.List;
import java.util.ArrayList;
import java.util.Iterator;
import java.util.Set;
import java.util.HashSet;
import java.io.StringReader;
import org.openrdf.repository.Repository;
import org.openrdf.repository.RepositoryResult;
import org.openrdf.repository.http.HTTPRepository;
import org.openrdf.OpenRDFException;
import org.openrdf.repository.RepositoryConnection;
import org.openrdf.query.TupleQuery;
import org.openrdf.query.TupleQueryResult;
import org.openrdf.query.BindingSet;
import org.openrdf.query.QueryLanguage;
import org.openrdf.rio.RDFFormat;
import org.openrdf.model.vocabulary.RDF;
import org.openrdf.model.vocabulary.RDFS;
import org.openrdf.model.ValueFactory;
import org.openrdf.model.URI;
import org.openrdf.model.Literal;
import org.openrdf.model.Statement;
import org.openrdf.http.protocol.transaction.operations.RemoveStatementsOperation;
import org.openrdf.repository.RepositoryException;
import org.openrdf.query.GraphQueryResult;
import org.openrdf.query.resultio.QueryResultIO;
import java.nio.charset.Charset;
import org.openrdf.query.resultio.TupleQueryResultFormat;
import org.openrdf.rio.RDFFormat;

class SesameConnector {
    
    private void get(RepositoryConnection con, String query) throws RepositoryException {
        try {
            query = "SELECT source FROM CONTEXT source " + query;

            TupleQuery tupleQuery = con.prepareTupleQuery(QueryLanguage.SERQL, query);
            TupleQueryResult result = tupleQuery.evaluate();
                
            try{
                List<String> bindingNames = result.getBindingNames();
                while (result.hasNext()) {
                    BindingSet bindingSet = result.next();
		    System.out.println(bindingSet.getValue(bindingNames.get(0)));
                }

            } finally {
                result.close();
            }
        } catch (org.openrdf.query.MalformedQueryException e) {
            System.out.print(e.getMessage());
	    System.exit(1);
        } catch (org.openrdf.query.QueryEvaluationException e) {
            System.out.print(e.getMessage());
	    System.exit(1);
        }
    }

    private void generic_get(RepositoryConnection con, String query) throws RepositoryException {
        try {
     
	    String query_type = query.trim().toLowerCase();
	    
	    if (query_type.startsWith("select")) {
		TupleQuery tupleQuery = con.prepareTupleQuery(QueryLanguage.SERQL, query);
		TupleQueryResult result = tupleQuery.evaluate();
                
		QueryResultIO res_out = new QueryResultIO(); 
		ByteArrayOutputStream out = new ByteArrayOutputStream();

		res_out.write(result, TupleQueryResultFormat.SPARQL , out); 
		System.out.println(out);

		try{
		    List<String> bindingNames = result.getBindingNames();
		    while (result.hasNext()) {    
			BindingSet bindingSet = result.next();
			Iterator<String> itr = bindingNames.iterator();
			while (itr.hasNext()) {
			    String name = itr.next();
			    System.out.println(name + ": " + bindingSet.getValue(name));
			}
		    }
		} finally {
		    result.close();
		}
	    } else if (query_type.startsWith("construct")) {
		
		GraphQueryResult graphResult = con.prepareGraphQuery(QueryLanguage.SERQL, query).evaluate();
		
		QueryResultIO res_out = new QueryResultIO(); 
		ByteArrayOutputStream out = new ByteArrayOutputStream();

		res_out.write(graphResult, RDFFormat.RDFXML, out); 
		System.out.println(out);
	    } else {
		System.exit(1);
	    }

        } catch (org.openrdf.query.MalformedQueryException e) {
	    System.out.print(e.getMessage());
            System.exit(1);
        } catch (org.openrdf.query.QueryEvaluationException e) {
            System.out.print(e.getMessage());
            System.exit(1);
        } catch (java.io.IOException e) {
            System.out.print(e.getMessage());
	    System.exit(1);
	} catch (org.openrdf.rio.RDFHandlerException e) {
            System.out.print(e.getMessage());
	    System.exit(1);
	} catch (org.openrdf.query.TupleQueryResultHandlerException e) {
            System.out.print(e.getMessage());
	    System.exit(1);
	}
    }


    private String get_owl_description(String repo, String query) {
	try {
	    String line;
	    Process p = Runtime.getRuntime().exec("/home/marcus/workspace/roboearth/SesameConnector/getOWLdescription.py " + repo + " " + query);
	    BufferedReader input = new BufferedReader(new InputStreamReader(p.getInputStream()));
	    String strOut = "";
	    while ((line = input.readLine()) != null) {
		strOut = strOut.concat(line);
	    }
	    System.out.println("OWL file: "+strOut);
	    input.close();
	    return strOut;
	}
	catch (Exception err) {
            System.out.print(err.getMessage());
	    err.printStackTrace();
	    return "error";
	}
    }

    private void test (String query) {
	System.out.println(get_owl_description("Recipes", query));
    }

    private String set(RepositoryConnection con, URI context, String uid, String repo) throws RepositoryException {
        try {
	    String data = get_owl_description(repo, uid);
   	    
	    StringReader input = new StringReader(data);
        con.add(input, "", RDFFormat.RDFXML, context);
        } catch (java.io.IOException e) {
	    System.out.println("BUG "+e.getMessage());
            System.exit(1);
        } catch (org.openrdf.rio.RDFParseException e) {
	    System.out.println("BUG2 "+e.getMessage()+" "+con+" "+context+" "+uid+" "+repo);
            System.exit(1);
        }

        return "set";
	    
    }

    private void rm(RepositoryConnection con, URI context) throws RepositoryException {
        RepositoryResult<Statement> statements = con.getStatements(null,null,null,true, context);
        while (statements.hasNext()) {
            Statement s = statements.next();
            RemoveStatementsOperation rmStatement = new RemoveStatementsOperation(s.getSubject(), s.getPredicate(), s.getObject(),context);
            rmStatement.execute(con);
        }
        
        System.out.println("rm");
    }

    private Repository getRepository(String sesameServer, String repositoryID) {
        return new HTTPRepository(sesameServer, repositoryID);
    }

    private void usage() {
        System.out.println("Usage:");
        System.out.println("get:  SesameConnector get [sesame server] [repository] [query]");
        System.out.println("generic_get:  SesameConnector generic_get [sesame server] [repository] [query]");
        System.out.println("set: SesameConnector set [sesame server] [repository] [context] [uid]");
        System.out.println("rm: SesameConnector rm [sesame server] [repository] [context]");
    }
 
    public static void main(String[] args) {
        SesameConnector sc = new SesameConnector();
 
        try {
            Repository myRepository = sc.getRepository(args[1], args[2]);
            myRepository.initialize();

            RepositoryConnection con = myRepository.getConnection();
            ValueFactory f = myRepository.getValueFactory();  

            try {
                if (args[0].equals("get")) sc.get(con, args[3]);
                else if (args[0].equals("generic_get")) sc.generic_get(con, args[3]);
                else if (args[0].equals("set"))  sc.set(con, f.createURI(args[3]), args[4], args[2]);
                else if (args[0].equals("rm")) sc.rm(con, f.createURI(args[3]));
                else {
                    sc.usage();
                } 
            } finally {
                con.close();
            }
        } catch (java.lang.ArrayIndexOutOfBoundsException e) {
            System.out.print(e.getMessage());
            sc.usage();
            System.exit(1);
        } catch (RepositoryException e) {
	    System.out.print(e.getMessage());
            System.exit(1);
        }
    }
}
