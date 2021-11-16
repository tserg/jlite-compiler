class Main {
	 Void main(){
	 	String s;
		SimpleMain sm;
		Bool r;
		Int i;
		sm = new SimpleMain();
		s = sm.getString("Hello there!");
		println(s);
		println("\n");
		i = 5;
		println(i);
		println("\n");
		readln(i);
		println(i);
	 }

 }

class SimpleMain {
	Bool c;

	String getString(String x){
		return "Aliens!";
	}

	Bool getC(Bool b) {
		c = false;
		return b;
	}
}
