class Main {
	 Void main(){
	 	Int i;
		Int j;
		Int k;
		Bool b;
		SimpleMain sm;
		String s;
		s = "Very difficult!";
		b = true;
		i = 2;
		j = i + 1; // j = 3
		k = 2 * 3; // k = 6
		sm = new SimpleMain();
		sm.a = 5;
		i = sm.add(17, 5, 2);
		s = "Most difficult!";
		println(i);		// should be -15
		println("\n");
		println(s);
		println("\n");
		println(b);
	 }

 }

class SimpleMain {
	Int a;
	Bool c;
	String d;

	Int add(Int x, Int y, Int z) {
		Int i;
		i = this.minus(z, x);
		println(i);		// should be 22
		println("\n");
		return y+x;
	}

	Int minus(Int x, Int y) {
		return x-y;
	}

	Int getA() {
		return a;
	}
}
