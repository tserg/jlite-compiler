class Main {
	 Void main(){
	 	Int i;
		Int k;
		Bool j;
		SimpleMain sm;

		sm = new SimpleMain();
		i = 5;
		k = 2;
		i = i + -k;
		j = false || true;
		println(j);
		println("\n");
		j = sm.getC(false);
		println(j);

		if (j) {
			println("Correct answer\n");
		} else {
			println("Wrong answer\n");
		}
	 }

 }

class SimpleMain {
	Bool c;

	String getString(String x){
		return x;
	}

	Bool getC(Bool b) {
		c = !b;
		println("GetC: ");
		println(c);
		println("\n");
		return c;
	}
}
