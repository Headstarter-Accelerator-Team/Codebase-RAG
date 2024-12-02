"use client";

import { Button } from "../ui/button";
import { Input } from "../ui/input";

export default function GithubForm(){
    return(<div className=" flex flex-row justify-between w-full h-20 bg-slate-600 p-5">
          <Input
            type="text"
            placeholder="Please enter github repo"
            className="w-2/3"
          />
          <Button>Submit</Button>
        </div>);
}