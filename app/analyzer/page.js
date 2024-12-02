"use client";
import { Button } from "@/components/ui/button";
import { Form } from "@/components/ui/form";
import { Input } from "@/components/ui/input";

export default function Analyzer() {
  return (
    <>
      <div id="header">
        <h1>Repository Analyzer</h1>
      </div>
      <div id="body" className="flex">
        <div className=" flex flex-row justify-between w-full h-20 bg-slate-600 p-5">
          <Input
            type="text"
            placeholder="Please enter github repo"
            className="w-2/3"
          />
          <Button>Submit</Button>
        </div>
      </div>
    </>
  );
}
