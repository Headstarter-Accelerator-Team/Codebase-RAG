import { Button } from "@/components/ui/button";
import { SignedIn, SignInButton } from "@clerk/nextjs";
import { SignedOut, SignIn } from "@clerk/nextjs";

export default function Home() {
  return (
    <>
      <div className="w-screen h-screen">
        <div id="header" className="flex flex-row justify-between w-full p-10">
          <h1 className="text-2xl">Repository Analyzer</h1>

          <SignedOut>
            <SignInButton>
              <Button>Sign In</Button>
            </SignInButton>
          </SignedOut>
          <SignedIn>
            <Button>Continue</Button>
          </SignedIn>
        </div>
        <div id="body"></div>
        <p></p>
      </div>
    </>
  );
}
